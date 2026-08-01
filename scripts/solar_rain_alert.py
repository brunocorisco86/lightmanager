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
RAIN_THROTTLE_SECONDS = 3600  # Trava de 1 hora para evitar múltiplos alertas no mesmo temporal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - RAIN_ALERT - %(message)s')

def check_abrupt_power_drop_and_rain(telemetry, previous_power_w, now_obj=None, dry_run=False):
    """
    Detecta queda abrupta de geração solar no horário de pico e cruza com a probabilidade
    de chuva da Open-Meteo para enviar um alerta preventivo no Telegram.
    """
    if not telemetry or previous_power_w is None:
        return False

    now = now_obj or datetime.now(BR_TZ)
    current_hour = now.hour
    current_power = float(telemetry.get("power_w") or 0.0)
    prev_power = float(previous_power_w)

    # 1. Valida se está no horário diurno de pico solar (10:00 às 16:30)
    if not (10 <= current_hour <= 16):
        return False

    # 2. Calcula se houve queda abrupta de geração (drop >= 50% e queda >= 750W quando prev >= 1000W)
    power_drop = prev_power - current_power
    if prev_power < 1000.0 or power_drop < 750.0 or (current_power / prev_power) > 0.50:
        return False

    # 3. Consulta dados de previsão do tempo (Open-Meteo) para confirmar probabilidade de chuva
    try:
        from scripts.solar_forecast import fetch_solar_forecast
    except ImportError:
        try:
            from solar_forecast import fetch_solar_forecast
        except ImportError:
            fetch_solar_forecast = None

    rain_probable = True  # Fallback preventivo caso a API esteja indisponível
    weather_cond = "Nebulosidade com chance de chuva"

    if fetch_solar_forecast:
        try:
            fc = fetch_solar_forecast()
            if fc and "today" in fc:
                today_fc = fc["today"]
                w_code = today_fc.get("weather_code", 0)
                weather_cond = today_fc.get("condition_full", weather_cond)
                # Códigos WMO de chuva/pancadas/chuvisco/tempestade
                if w_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99, 3, 45, 48]:
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

    now_ts = time.time()
    if not dry_run and (now_ts - throttle_time < RAIN_THROTTLE_SECONDS):
        logging.info("⏳ Alerta de chuva suprimido pelo controle de rate-limiting (menos de 1 hora).")
        return False

    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_user_id = os.getenv("TELEGRAM_ALLOWED_USER_ID")

    alert_msg = (
        f"🌧️ *ALERTA PREVENTIVO DE CHUVA*\n\n"
        f"⚡ *Queda Abrupta de Geração Solar:* `{int(prev_power)} W` ➡️ `{int(current_power)} W` (Drop de `{int(power_drop)} W`)\n"
        f"☁️ *Condição do Tempo:* {weather_cond}\n"
        f"📅 *Horário:* `{now.strftime('%H:%M')}`\n\n"
        f"💡 *Recomendação:* Alta probabilidade de chuva nas próximas horas! "
        f"Lembre-se de levar guarda-chuva se for sair para não se molhar no caminho dos seus compromissos! ☔"
    )

    logging.warning(f"🌧️ Alerta preventivo de chuva disparado! Drop de {int(power_drop)} W")

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
    telemetry_sample = {"power_w": 350.0}
    check_abrupt_power_drop_and_rain(telemetry_sample, previous_power_w=2200.0, dry_run=True)
