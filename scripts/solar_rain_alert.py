import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

BR_TZ = timezone(timedelta(hours=-3))
RAIN_THROTTLE_FILE = "/tmp/rain_alert_throttle.json"
POWER_HISTORY_FILE = "/tmp/solar_power_history.json"
RAIN_THROTTLE_SECONDS = 3600  # Trava de 1 hora para evitar múltiplos alertas no mesmo temporal
HISTORY_WINDOW_SECONDS = 1200  # 20 minutos de histórico deslizante

logging.basicConfig(level=logging.INFO, format='%(asctime)s - RAIN_ALERT - %(message)s')

def update_and_get_power_history(current_power, now_ts):
    """
    Mantém histórico de potência solar dos últimos 20 minutos em disco.
    """
    history = []
    if os.path.exists(POWER_HISTORY_FILE):
        try:
            with open(POWER_HISTORY_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    history = [item for item in data if isinstance(item, dict) and (now_ts - float(item.get("ts", 0)) <= HISTORY_WINDOW_SECONDS)]
        except Exception:
            history = []

    history.append({"ts": now_ts, "power_w": float(current_power)})
    try:
        with open(POWER_HISTORY_FILE, "w") as f:
            json.dump(history, f)
    except Exception as e:
        logging.warning(f"Erro ao salvar histórico de potência: {e}")
    return history

def check_abrupt_power_drop_and_rain(telemetry, previous_power_w=None, now_obj=None, dry_run=False):
    """
    Detecta queda abrupta ou progressiva de geração solar no horário diurno (janela de 20 min)
    e cruza com a previsão meteorológica da Open-Meteo para enviar um alerta preventivo no Telegram.
    """
    if not telemetry:
        return False

    now = now_obj or datetime.now(BR_TZ)
    now_ts = now.timestamp()
    current_hour = now.hour
    current_minute = now.minute
    time_float = current_hour + current_minute / 60.0
    current_power = float(telemetry.get("power_w") or 0.0)
    prev_power = float(previous_power_w) if previous_power_w is not None else current_power
    status = (telemetry.get("status") or "Normal").strip().lower()

    # 1. Valida se está no horário diurno de geração solar (08:00 às 17:15)
    if not (8.0 <= time_float <= 17.25):
        return False

    # Carrega/Atualiza janela deslizante de 20 minutos
    if not dry_run:
        history = update_and_get_power_history(current_power, now_ts)
        recent_powers = [float(entry["power_w"]) for entry in history]
    else:
        recent_powers = [current_power]

    if previous_power_w is not None:
        recent_powers.append(prev_power)

    peak_power_20min = max(recent_powers)

    # 2. Requisitos do Guardrail:
    # A) Queda abrupta de 1 minuto: prev_power >= 300W e drop_1min >= 200W e current_power <= 120W
    power_drop_1min = prev_power - current_power
    is_abrupt_1min_drop = (prev_power >= 300.0 and power_drop_1min >= 200.0 and current_power <= 120.0)

    # B) Queda progressiva/acentuada na janela de 20 minutos (ex: 610W -> 90W em 15 min):
    # Pico recente de pelo menos 300W, queda total >= 200W, potência atual <= 120W e queda >= 50%
    power_drop_window = peak_power_20min - current_power
    drop_pct = ((peak_power_20min - current_power) / peak_power_20min * 100.0) if peak_power_20min > 0 else 0
    is_window_drop = (peak_power_20min >= 300.0 and power_drop_window >= 200.0 and current_power <= 120.0 and drop_pct >= 50.0)

    # C) Sistema entrando em status 'Waiting' durante o dia após ter gerado >= 200W recentemente
    is_waiting_during_day = (status == "waiting" and peak_power_20min >= 200.0)

    if not (is_abrupt_1min_drop or is_window_drop or is_waiting_during_day):
        return False

    display_peak = peak_power_20min if is_window_drop else (prev_power if is_abrupt_1min_drop else peak_power_20min)
    display_drop = display_peak - current_power
    display_drop_pct = ((display_peak - current_power) / display_peak * 100.0) if display_peak > 0 else 0.0

    # 3. Consulta dados de previsão do tempo (Open-Meteo) para confirmar probabilidade de chuva
    try:
        from scripts.solar_forecast import fetch_solar_forecast
    except ImportError:
        try:
            from solar_forecast import fetch_solar_forecast
        except ImportError:
            fetch_solar_forecast = None

    rain_probable = True  # Fallback preventivo caso a API esteja indisponível
    weather_cond = "Céu encoberto com alta probabilidade de chuva"

    if fetch_solar_forecast:
        try:
            fc = fetch_solar_forecast()
            if fc and "today" in fc:
                today_fc = fc["today"]
                w_code = today_fc.get("weather_code", 0)
                weather_cond = today_fc.get("condition_full", weather_cond)
                # Códigos WMO de nuvens/chuva/pancadas/chuvisco/tempestade
                if w_code in [2, 3, 45, 48, 51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99]:
                    rain_probable = True
                else:
                    # Se o WMO diário for ensolarado, porém a queda real em solo foi >50% até <=120W,
                    # mantemos o alerta preventivo ativado devido ao evento local em andamento.
                    rain_probable = True
        except Exception as efc:
            logging.warning(f"Não foi possível confirmar chuva no Open-Meteo: {efc}")

    if not rain_probable:
        return False

    # 4. Trava de Rate-Limiting / Throttle (1 hora)
    throttle_time = 0
    if os.path.exists(RAIN_THROTTLE_FILE):
        try:
            with open(RAIN_THROTTLE_FILE, "r") as f:
                data = json.load(f)
                throttle_time = float(data.get("last_rain_alert", 0))
        except Exception:
            throttle_time = 0

    if not dry_run and (now_ts - throttle_time < RAIN_THROTTLE_SECONDS):
        logging.info("⏳ Alerta de chuva suprimido pelo controle de rate-limiting (menos de 1 hora).")
        return False

    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_user_id = os.getenv("TELEGRAM_ALLOWED_USER_ID")

    alert_msg = (
        f"🌧️ *ALERTA PREVENTIVO DE CHUVA*\n\n"
        f"⚡ *Queda de Geração Solar:* `{int(display_peak)} W` ➡️ `{int(current_power)} W` (Queda de `{int(display_drop)} W` / `{display_drop_pct:.0f}%`)\n"
        f"☁️ *Condição do Tempo:* {weather_cond}\n"
        f"📅 *Horário:* `{now.strftime('%H:%M')}`\n\n"
        f"💡 *Recomendação:* Alta probabilidade de chuva nas próximas horas! "
        f"Lembre-se de levar guarda-chuva se for sair para não se molhar no caminho dos seus compromissos! ☔"
    )

    logging.warning(f"🌧️ Alerta preventivo de chuva disparado! Queda de {int(display_drop)} W ({display_drop_pct:.0f}%)")

    if dry_run:
        print("=== [DRY-RUN] Alerta Preventivo de Chuva ===")
        print(alert_msg)
        return True

    if tg_token and tg_user_id:
        try:
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={"chat_id": tg_user_id, "text": alert_msg, "parse_mode": "Markdown"},
                timeout=10
            )
            logging.info("✅ Alerta de chuva enviado com sucesso para o Telegram!")
        except Exception as etg:
            logging.error(f"Erro ao enviar alerta de chuva no Telegram: {etg}")

    try:
        with open(RAIN_THROTTLE_FILE, "w") as f:
            json.dump({"last_rain_alert": now_ts}, f)
    except Exception as e:
        logging.warning(f"Erro ao atualizar rain throttle file: {e}")

    return True

if __name__ == "__main__":
    telemetry_sample = {"power_w": 90.0, "status": "Normal"}
    check_abrupt_power_drop_and_rain(telemetry_sample, previous_power_w=610.0, dry_run=True)
