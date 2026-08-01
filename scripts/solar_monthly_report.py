import os
import sys
import json
import logging
import argparse
import calendar
import requests
import psycopg2
from datetime import datetime, timedelta, date, timezone

# 1. Configuração do Backend Headless do Matplotlib ANTES de importar pyplot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

BR_TZ = timezone(timedelta(hours=-3))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SOLAR_MONTHLY_REPORT - %(message)s')

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

def get_target_month_range(now_dt=None):
    """
    Retorna (year, month, month_name, days_in_month) para o mês anterior em relação à data atual.
    """
    now = now_dt or datetime.now(BR_TZ)
    first_day_this_month = now.date().replace(day=1)
    last_day_prev_month = first_day_this_month - timedelta(days=1)
    year = last_day_prev_month.year
    month = last_day_prev_month.month
    days_in_month = calendar.monthrange(year, month)[1]
    
    month_names_pt = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    month_name = month_names_pt[month]
    return year, month, month_name, days_in_month

def fetch_monthly_solar_data(year, month, conn=None):
    """
    Busca todas as métricas agregadas por dia para o ano e mês especificados.
    """
    local_conn = False
    if conn is None:
        conn = get_db_conn()
        local_conn = True

    days_in_month = calendar.monthrange(year, month)[1]
    daily_records = {d: {"kwh": 0.0, "max_w": 0.0, "avg_temp": 0.0} for d in range(1, days_in_month + 1)}

    if not conn:
        return daily_records

    try:
        start_date = date(year, month, 1)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    EXTRACT(DAY FROM (timestamp AT TIME ZONE 'America/Sao_Paulo'))::int AS day_num,
                    COALESCE(MAX(today_kwh), 0.0) AS max_today_kwh,
                    COALESCE(MAX(power_w), 0.0) AS max_power_w,
                    COALESCE(AVG(temperature), 0.0) AS avg_temp
                FROM solar_generation
                WHERE DATE_TRUNC('month', timestamp AT TIME ZONE 'America/Sao_Paulo') = DATE_TRUNC('month', %s::date)
                GROUP BY day_num
                ORDER BY day_num ASC;
            """, (start_date,))
            rows = cur.fetchall()

            for row in rows:
                day_num, max_kwh, max_w, avg_temp = row
                if 1 <= day_num <= days_in_month:
                    daily_records[day_num] = {
                        "kwh": float(max_kwh),
                        "max_w": float(max_w),
                        "avg_temp": float(avg_temp)
                    }
    except Exception as e:
        logging.error(f"Erro ao buscar dados mensais no banco: {e}")
    finally:
        if local_conn:
            conn.close()

    return daily_records

def get_tariff_rate(conn=None):
    """
    Obtém a tarifa da concessionária (R$/kWh) gravada no DB ou parâmetro local.
    """
    tariff = 0.85
    tax_rate = float(os.getenv("ENERGY_TAX_RATE", "0.25"))

    local_conn = False
    if conn is None:
        conn = get_db_conn()
        local_conn = True

    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT total_rate FROM energy_tariffs ORDER BY effective_date DESC LIMIT 1;")
                row = cur.fetchone()
                if row and row[0]:
                    tariff = float(row[0])
        except Exception:
            pass
        finally:
            if local_conn:
                conn.close()

    return tariff * (1.0 + tax_rate)

def render_monthly_chart(year, month, month_name, daily_data):
    """
    Gera o gráfico de barras mensal da geração diária (kWh) usando Matplotlib headless.
    """
    days = sorted(daily_data.keys())
    kwh_values = [daily_data[d]["kwh"] for d in days]
    total_kwh = sum(kwh_values)
    avg_kwh = total_kwh / len(days) if days else 0.0

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5), dpi=130)
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#1e293b')

    bars = ax.bar(days, kwh_values, color='#f59e0b', edgecolor='#d97706', alpha=0.85, width=0.7, label='Geração Diária (kWh)')

    max_kwh = max(kwh_values) if kwh_values else 0.0
    if max_kwh > 0:
        max_idx = kwh_values.index(max_kwh)
        bars[max_idx].set_color('#fbbf24')
        bars[max_idx].set_edgecolor('#ffffff')
        bars[max_idx].set_linewidth(1.5)

    ax.axhline(avg_kwh, color='#38bdf8', linestyle='--', linewidth=1.8, label=f'Média Mensal: {avg_kwh:.1f} kWh/dia')

    ax.set_title(f'Geração Solar Mensal - {month_name}/{year} (Total: {total_kwh:.1f} kWh)', fontsize=14, color='#f8fafc', fontweight='bold', pad=15)
    ax.set_xlabel('Dia do Mês', fontsize=11, color='#94a3b8')
    ax.set_ylabel('Energia Gerada (kWh)', fontsize=11, color='#94a3b8')

    ax.set_xticks(range(1, len(days) + 1, 2 if len(days) > 20 else 1))
    ax.tick_params(colors='#94a3b8')
    ax.grid(axis='y', color='#334155', linestyle=':', alpha=0.6)

    ax.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#f8fafc', loc='upper right')
    plt.tight_layout()

    out_path = f"/tmp/solar_monthly_report_{year}_{month:02d}.png"
    plt.savefig(out_path, dpi=130, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    return out_path

SOLAR_CONSULTANT_SYSTEM_PROMPT = (
    "Você é um Engenheiro Consultor de Eficiência Energética e Gestor de Ativos Solares. "
    "Sua missão é analisar o relatório consolidado de produção mensal de energia fotovoltaica "
    "e gerar um parecer executivo para o proprietário da usina doméstica.\n\n"
    "Diretrizes da resposta:\n"
    "1. Formate em Markdown amigável para o Telegram com bullet points e emojis.\n"
    "2. Divida em 4 seções objetivas:\n"
    "   - 📊 *Desempenho Geral e Eficiência da Usina*\n"
    "   - 💰 *Economia Financeira e Estimativa na Fatura (R$)*\n"
    "   - ⚡ *Saúde Operacional do Inversor & Ocorrências*\n"
    "   - 💡 *Recomendações Estratégicas para o Próximo Mês*\n"
    "3. Mantenha o parecer direto, focado nos resultados econômicos e técnicos (máximo 200 palavras)."
)

def generate_ai_monthly_consultant_report(summary_data):
    """
    Comprime o contexto e invoca o Agente Consultor IA (Gemini API) para emitir parecer mensal.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")

    prompt_context = (
        f"DADOS DE PRODUÇÃO SOLAR DO MÊS ({summary_data['month_name']}/{summary_data['year']}):\n"
        f"- Geração Acumulada no Mês: {summary_data['total_kwh']:.2f} kWh\n"
        f"- Média Diária de Geração: {summary_data['avg_kwh']:.2f} kWh/dia\n"
        f"- Dia de Maior Produção: Dia {summary_data['best_day']} ({summary_data['best_kwh']:.2f} kWh)\n"
        f"- Dia de Menor Produção: Dia {summary_data['worst_day']} ({summary_data['worst_kwh']:.2f} kWh)\n"
        f"- Potência de Pico Máxima Registrada: {summary_data['peak_w']:.0f} W\n"
        f"- Economia Financeira Estimada na Fatura: R$ {summary_data['savings_brl']:.2f} (Tarifa: R$ {summary_data['tariff_rate']:.2f}/kWh)\n"
        f"- Total de Dias Ativos no Mês: {summary_data['active_days']} dias\n"
    )

    if not gemini_key:
        fallback_msg = (
            f"👷‍♂️ *Parecer do Consultor Solar (IA)*\n\n"
            f"⚠️ *Nota:* A `GEMINI_API_KEY` não está configurada no `.env` do servidor.\n"
            f"Para ativar o parecer inteligente da IA Gemini nos relatórios mensais, adicione a chave no `.env`."
        )
        return fallback_msg

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": gemini_key
    }
    payload = {
        "contents": [{
            "parts": [
                {"text": SOLAR_CONSULTANT_SYSTEM_PROMPT},
                {"text": prompt_context}
            ]
        }]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code == 200:
            res_data = res.json()
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            logging.error(f"Erro na API Gemini (HTTP {res.status_code}): {res.text}")
    except Exception as e:
        logging.error(f"Exceção ao gerar parecer mensal do Consultor IA: {e}")

    return (
        f"👷‍♂️ *Parecer do Consultor Solar*\n\n"
        f"A usina operou com geração total de `{summary_data['total_kwh']:.1f} kWh` "
        f"com economia estimada em `R$ {summary_data['savings_brl']:.2f}`."
    )

def send_monthly_telegram_report(photo_path, summary_data, ai_report_text, dry_run=False):
    """
    Envia a imagem PNG do gráfico mensal e a mensagem com o parecer técnico no Telegram.
    """
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_user_id = os.getenv("TELEGRAM_ALLOWED_USER_ID")

    caption = (
        f"📊 *RELATÓRIO MENSAL DE PRODUÇÃO SOLAR*\n"
        f"🗓️ *Período:* `{summary_data['month_name']}/{summary_data['year']}`\n\n"
        f"⚡ *Geração Acumulada:* `{summary_data['total_kwh']:.1f} kWh`\n"
        f"📈 *Média Diária:* `{summary_data['avg_kwh']:.1f} kWh/dia`\n"
        f"🏆 *Melhor Dia (Dia {summary_data['best_day']}):* `{summary_data['best_kwh']:.1f} kWh`\n"
        f"💰 *Economia Estimada:* `R$ {summary_data['savings_brl']:.2f}`\n\n"
        f"---"
    )

    full_message = f"{caption}\n\n{ai_report_text}"

    if dry_run:
        print("=== [DRY-RUN] Envio do Relatório Mensal Telegram ===")
        print(f"Foto: {photo_path}")
        print(full_message)
        return True

    if tg_token and tg_user_id:
        try:
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as photo_file:
                    requests.post(
                        f"https://api.telegram.org/bot{tg_token}/sendPhoto",
                        data={"chat_id": tg_user_id, "caption": caption, "parse_mode": "Markdown"},
                        files={"photo": photo_file},
                        timeout=20
                    )
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={"chat_id": tg_user_id, "text": ai_report_text, "parse_mode": "Markdown"},
                timeout=15
            )
            logging.info("✅ Relatório Mensal Solar enviado com sucesso para o Telegram!")
            return True
        except Exception as e:
            logging.error(f"Erro ao enviar relatório mensal no Telegram: {e}")

    return False

def run_monthly_report_flow(year=None, month=None, dry_run=False):
    """
    Orquestrador principal do relatório mensal.
    """
    if year is None or month is None:
        year, month, month_name, days_in_month = get_target_month_range()
    else:
        month_names_pt = [
            "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        month_name = month_names_pt[month]
        days_in_month = calendar.monthrange(year, month)[1]

    logging.info(f"☀️ Gerando Relatório Mensal de Produção Solar para {month_name}/{year}...")

    daily_data = fetch_monthly_solar_data(year, month)
    tariff_rate = get_tariff_rate()

    kwh_list = [daily_data[d]["kwh"] for d in daily_data]
    total_kwh = sum(kwh_list)
    avg_kwh = total_kwh / len(daily_data) if daily_data else 0.0
    active_days = sum(1 for d in daily_data if daily_data[d]["kwh"] > 0.1)

    peak_w = max([daily_data[d]["max_w"] for d in daily_data]) if daily_data else 0.0
    best_day = max(daily_data, key=lambda d: daily_data[d]["kwh"]) if daily_data else 1
    best_kwh = daily_data[best_day]["kwh"] if daily_data else 0.0

    worst_day = min(daily_data, key=lambda d: daily_data[d]["kwh"]) if daily_data else 1
    worst_kwh = daily_data[worst_day]["kwh"] if daily_data else 0.0

    savings_brl = total_kwh * tariff_rate

    summary_data = {
        "year": year,
        "month": month,
        "month_name": month_name,
        "days_in_month": days_in_month,
        "total_kwh": total_kwh,
        "avg_kwh": avg_kwh,
        "active_days": active_days,
        "peak_w": peak_w,
        "best_day": best_day,
        "best_kwh": best_kwh,
        "worst_day": worst_day,
        "worst_kwh": worst_kwh,
        "tariff_rate": tariff_rate,
        "savings_brl": savings_brl
    }

    chart_path = render_monthly_chart(year, month, month_name, daily_data)
    ai_report = generate_ai_monthly_consultant_report(summary_data)

    success = send_monthly_telegram_report(chart_path, summary_data, ai_report, dry_run=dry_run)
    return summary_data, chart_path, ai_report, success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Relatório Mensal de Produção Solar")
    parser.add_argument("--force", action="store_true", help="Força a execução independente da data")
    parser.add_argument("--dry-run", action="store_true", help="Executa sem enviar mensagens no Telegram")
    parser.add_argument("--month", type=int, help="Mês específico (1-12)")
    parser.add_argument("--year", type=int, help="Ano específico (ex: 2026)")

    args = parser.parse_args()
    run_monthly_report_flow(year=args.year, month=args.month, dry_run=args.dry_run)
