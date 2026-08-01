import os
import sys
import json
import logging
import argparse
import requests
import psycopg2
from datetime import datetime, timedelta, date, timezone

# 1. Configuração do Backend Headless do Matplotlib ANTES de importar pyplot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from dotenv import load_dotenv

# Carrega variáveis de ambiente
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

# Timezone de Brasília (GMT-3)
BR_TZ = timezone(timedelta(hours=-3))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SOLAR_REPORT - %(message)s')

def get_db_conn():
    try:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            conn = psycopg2.connect(db_url)
        else:
            conn = psycopg2.connect(
                database=os.getenv("POSTGRES_DB", "light_manager"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5432")
            )
        with conn.cursor() as cur:
            cur.execute("SET timezone TO 'America/Sao_Paulo';")
        return conn
    except Exception as e:
        logging.error(f"Erro ao conectar ao PostgreSQL: {e}")
        return None

def fetch_daily_solar_data(target_date=None, conn=None):
    """
    Busca todas as entradas de telemetria solar registradas no banco para o dia especificado.
    """
    if target_date is None:
        target_date = datetime.now(BR_TZ).date()

    local_conn = False
    if conn is None:
        conn = get_db_conn()
        local_conn = True

    if not conn:
        return []

    records = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp, power_w, today_kwh, total_kwh,
                       pv1_voltage, pv1_current, pv2_voltage, pv2_current,
                       grid_voltage, temperature, status
                FROM solar_generation
                WHERE DATE(timestamp AT TIME ZONE 'America/Sao_Paulo') = %s
                ORDER BY timestamp ASC;
            """, (target_date,))
            rows = cur.fetchall()

            for r in rows:
                records.append({
                    "timestamp": r[0].astimezone(BR_TZ),
                    "power_w": float(r[1]) if r[1] is not None else 0.0,
                    "today_kwh": float(r[2]) if r[2] is not None else 0.0,
                    "total_kwh": float(r[3]) if r[3] is not None else 0.0,
                    "pv1_voltage": float(r[4]) if r[4] is not None else 0.0,
                    "pv1_current": float(r[5]) if r[5] is not None else 0.0,
                    "pv2_voltage": float(r[6]) if r[6] is not None else 0.0,
                    "pv2_current": float(r[7]) if r[7] is not None else 0.0,
                    "grid_voltage": float(r[8]) if r[8] is not None else 0.0,
                    "temperature": float(r[9]) if r[9] is not None else 0.0,
                    "status": r[10] or "Normal"
                })
    except Exception as e:
        logging.error(f"Erro ao buscar dados de geração solar no DB: {e}")
    finally:
        if local_conn and conn:
            conn.close()

    return records

def calculate_daily_summary(records, target_date=None):
    """
    Calcula os indicadores resumidos (KPIs) da geração do dia.
    """
    if target_date is None:
        target_date = datetime.now(BR_TZ).date()

    if not records:
        return {
            "date": target_date.strftime("%d/%m/%Y"),
            "today_kwh": 0.0,
            "peak_power_w": 0.0,
            "peak_time": None,
            "max_temp": 0.0,
            "start_time": None,
            "end_time": None,
            "record_count": 0
        }

    max_kwh = max((r["today_kwh"] for r in records), default=0.0)
    peak_record = max(records, key=lambda x: x["power_w"], default=records[0])
    max_temp = max((r["temperature"] for r in records if r["temperature"] > 0), default=0.0)

    # Identifica horário de início e fim da geração (> 10W)
    active_records = [r for r in records if r["power_w"] >= 10.0]
    start_time = active_records[0]["timestamp"].strftime("%H:%M") if active_records else None
    end_time = active_records[-1]["timestamp"].strftime("%H:%M") if active_records else None

    return {
        "date": target_date.strftime("%d/%m/%Y"),
        "today_kwh": max_kwh,
        "peak_power_w": peak_record["power_w"],
        "peak_time": peak_record["timestamp"].strftime("%H:%M") if peak_record["power_w"] > 0 else None,
        "max_temp": max_temp,
        "start_time": start_time,
        "end_time": end_time,
        "record_count": len(records)
    }

def generate_solar_chart_png(records, summary, output_path="/tmp/solar_report_today.png"):
    """
    Gera o gráfico da curva sino de potência solar fotovoltaica usando Matplotlib Headless (Agg).
    """
    if not records:
        logging.warning("Nenhum registro para gerar o gráfico solar.")
        return None

    # Configuração de estilo escuro combinando com a UI Web (--bg: #0f172a, --card: #1e293b)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#1e293b')

    timestamps = [r["timestamp"] for r in records]
    powers = [r["power_w"] for r in records]

    # Plota a linha de potência e área preenchida sob a curva
    ax.plot(timestamps, powers, color='#fbbf24', linewidth=2.5, label='Potência (W)')
    ax.fill_between(timestamps, powers, color='#fbbf24', alpha=0.25)

    # Destaque para o ponto de potência pico
    if summary["peak_power_w"] > 0:
        peak_record = max(records, key=lambda x: x["power_w"])
        ax.plot(peak_record["timestamp"], peak_record["power_w"], marker='o', markersize=8, color='#ef4444')
        ax.annotate(
            f"Pico: {int(summary['peak_power_w'])} W\n({summary['peak_time']})",
            xy=(peak_record["timestamp"], peak_record["power_w"]),
            xytext=(15, 15),
            textcoords='offset points',
            arrowprops=dict(arrowstyle='->', color='#ef4444', lw=1.5),
            fontsize=9,
            color='#f8fafc',
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#0f172a', edgecolor='#ef4444', alpha=0.8)
        )

    # Título e Rótulos
    ax.set_title(f"Geração Solar Fotovoltaica — {summary['date']}", fontsize=13, color='#fbbf24', fontweight='bold', pad=15)
    ax.set_xlabel("Horário (GMT-3)", fontsize=10, color='#94a3b8')
    ax.set_ylabel("Potência (W)", fontsize=10, color='#94a3b8')

    # Formatação do Eixo X (Hora:Minuto)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=BR_TZ))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    fig.autofmt_xdate()

    # Formatação de Grid e Spines
    ax.grid(True, linestyle='--', alpha=0.3, color='#475569')
    for spine in ax.spines.values():
        spine.set_color('#334155')

    # Caixa Informativa de Resumo
    info_text = (
        f"Hoje Gerado: {summary['today_kwh']:.2f} kWh\n"
        f"Potencia Pico: {int(summary['peak_power_w'])} W\n"
        f"Janela Ativa: {summary['start_time'] or '--'} as {summary['end_time'] or '--'}\n"
        f"Temp Max: {summary['max_temp']:.1f} °C"
    )
    ax.text(
        0.02, 0.95, info_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='top',
        color='#f8fafc',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#0f172a', edgecolor='#38bdf8', alpha=0.85)
    )

    plt.tight_layout()
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    logging.info(f"🎨 Gráfico solar PNG gerado com sucesso em: {output_path}")
    return output_path

def send_daily_solar_telegram_report(target_date=None, dry_run=False, conn=None):
    """
    Gera e envia o relatório diário de produção solar fotovoltaica para o Telegram.
    """
    if target_date is None:
        target_date = datetime.now(BR_TZ).date()

    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_user_id = os.getenv("TELEGRAM_ALLOWED_USER_ID")

    records = fetch_daily_solar_data(target_date, conn=conn)
    summary = calculate_daily_summary(records, target_date)

    chart_path = generate_solar_chart_png(records, summary)

    peak_time_str = f" (às `{summary['peak_time']}`)" if summary.get('peak_time') else ""
    caption = (
        f"☀️ *Relatório Diário de Geração Solar*\n"
        f"📅 Data: `{summary['date']}`\n\n"
        f"📊 *Métricas de Produção*\n"
        f"⚡ *Potência Pico:* `{int(summary['peak_power_w'])} W`{peak_time_str}\n"
        f"🔋 *Energia Gerada:* `{summary['today_kwh']:.2f} kWh`\n"
        f"⏱ *Janela Ativa:* `{summary['start_time'] or 'N/A'}` às `{summary['end_time'] or 'N/A'}`\n"
        f"🌡 *Temp. Máx Inversor:* `{summary['max_temp']:.1f} °C`"
    )

    if dry_run:
        print("=== [DRY-RUN] Relatório Telegram ===")
        print(caption)
        print(f"Caminho do Gráfico: {chart_path}")
        return True

    if not tg_token or not tg_user_id:
        logging.warning("TELEGRAM_BOT_TOKEN ou TELEGRAM_ALLOWED_USER_ID não configurados.")
        return False

    url = f"https://api.telegram.org/bot{tg_token}/sendPhoto"
    payload = {
        "chat_id": tg_user_id,
        "caption": caption,
        "parse_mode": "Markdown"
    }

    try:
        if chart_path and os.path.exists(chart_path):
            with open(chart_path, "rb") as photo_file:
                files = {"photo": photo_file}
                resp = requests.post(url, data=payload, files=files, timeout=15)
        else:
            # Fallback para mensagem de texto caso o gráfico falhe
            msg_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            resp = requests.post(msg_url, json={"chat_id": tg_user_id, "text": caption, "parse_mode": "Markdown"}, timeout=10)

        if resp.status_code == 200:
            logging.info("✅ Relatório diário de geração solar enviado com sucesso via Telegram!")
            return True
        else:
            logging.error(f"Erro ao enviar relatório no Telegram: HTTP {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        logging.error(f"Falha na requisição para o Telegram: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerador de Relatório Solar Pós-Pôr do Sol")
    parser.add_argument("--date", type=str, help="Data no formato YYYY-MM-DD (Padrão: Hoje)")
    parser.add_argument("--dry-run", action="store_true", help="Gera o relatório e gráfico sem enviar no Telegram")
    args = parser.parse_args()

    target_d = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else datetime.now(BR_TZ).date()
    send_daily_solar_telegram_report(target_date=target_d, dry_run=args.dry_run)
