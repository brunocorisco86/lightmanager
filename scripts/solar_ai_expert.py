import os
import sys
import json
import logging
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

BR_TZ = timezone(timedelta(hours=-3))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SOLAR_AI_EXPERT - %(message)s')

SOLAR_EXPERT_SYSTEM_PROMPT = (
    "Você é um Engenheiro Eletricista Sênior especialista em Sistemas Fotovoltaicos On-Grid, "
    "Arranjos de Placas Solares (PV) e Inversores de String. "
    "Sua função é analisar alertas de anomalias operacionais reportadas na LAN e fornecer um "
    "diagnóstico técnico rápido, prático e fundamentado para o proprietário do sistema.\n\n"
    "GUARDRAILS CLIMÁTICOS E OPERACIONAIS OBRIGATÓRIOS:\n"
    "1. CORRELAÇÃO METEOROLÓGICA: Sempre analise a 'CONDIÇÃO CLIMÁTICA ATUAL NO LOCAL' e a 'Potência Gerada Atual' antes de indicar causas ou ações.\n"
    "2. CÉU ENCOBERTO / CHUVA / BAIXA IRRADIAÇÃO (< 200W): Se a potência gerada estiver baixa (< 200W) ou houver chuva, nebulosidade alta ou céu encoberto, "
    "informe com clareza que a queda de corrente/tensão em uma das strings (MPPT) é um comportamento NORMAL de ajuste dinâmico do inversor sob pouca luz. "
    "NUNCA oriente a chamar suporte técnico, instalador ou manutenção presencial caso a causa seja apenas chuva, nuvens ou céu encoberto!\n"
    "3. SUPORTE TÉCNICO E MANUTENÇÃO: Somente sugira acionar suporte técnico ou instalador se houver sol pleno com potência alta (>= 200W) e assimetria persistente em uma string, "
    "sobretemperatura crítica (>= 60°C) ou código de erro interno irrecuperável no inversor.\n\n"
    "Diretrizes de resposta:\n"
    "1. Formate em Markdown amigável para o Telegram com bullet points e emojis.\n"
    "2. Estruture em 3 seções curtas:\n"
    "   - 🧠 *Diagnóstico da Causa Raiz* (correlacione a telemetria às condições climáticas locais atuais).\n"
    "   - 🛠️ *Ações Recomendadas de Verificação* (se for chuva/céu encoberto, oriente apenas aguardar a abertura do sol; priorize segurança elétrica se houver inspeção necessária).\n"
    "   - ⚠️ *Nível de Risco Operacional* (BAIXO, MÉDIO ou CRÍTICO).\n"
    "3. Seja conciso (máximo 160 palavras). Não use saudações longas."
)

def analyze_solar_anomaly_with_ai(anomaly_info, telemetry, dry_run=False):
    """
    Invoca o Agente Especialista Fotovoltaico (Gemini AI) para analisar a anomalia solar
    correlacionando a telemetria aos dados climáticos atuais do local e envia o parecer no Telegram.
    """
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_user_id = os.getenv("TELEGRAM_ALLOWED_USER_ID")
    gemini_key = os.getenv("GEMINI_API_KEY")

    now_str = datetime.now(BR_TZ).strftime("%d/%m/%Y %H:%M:%S")

    # Busca previsão / condição meteorológica atual para correlação climática
    weather_cond = "Não disponível"
    try:
        from scripts.solar_forecast import fetch_solar_forecast
    except ImportError:
        try:
            from solar_forecast import fetch_solar_forecast
        except ImportError:
            fetch_solar_forecast = None

    if fetch_solar_forecast:
        try:
            fc = fetch_solar_forecast()
            if fc and "today" in fc:
                weather_cond = fc["today"].get("condition_full", weather_cond)
        except Exception as efc:
            logging.warning(f"Não foi possível obter dados de tempo para o Agente IA: {efc}")

    prompt_context = (
        f"ANOMALIA DETECTADA NO INVERSOR SOLAR:\n"
        f"- Título do Alerta: {anomaly_info.get('title')}\n"
        f"- Detalhe: {anomaly_info.get('detail')}\n"
        f"- Horário da Ocorrência: {now_str}\n\n"
        f"CONDIÇÃO CLIMÁTICA ATUAL NO LOCAL:\n"
        f"- Tempo / Nebulosidade: {weather_cond}\n\n"
        f"TELEMETRIA COMPLETA DO INVERSOR:\n"
        f"- Potência Gerada Atual: {telemetry.get('power_w', 0)} W\n"
        f"- Energia Gerada Hoje: {telemetry.get('today_kwh', 0)} kWh\n"
        f"- Temperatura Interna: {telemetry.get('temperature', '--')} °C\n"
        f"- String PV1 (DC): {telemetry.get('pv1_voltage', '--')} V / {telemetry.get('pv1_current', '--')} A\n"
        f"- String PV2 (DC): {telemetry.get('pv2_voltage', '--')} V / {telemetry.get('pv2_current', '--')} A\n"
        f"- Rede AC (Grid): {telemetry.get('grid_voltage', '--')} V / {telemetry.get('grid_current', '--')} A ({telemetry.get('grid_frequency', '--')} Hz)\n"
        f"- Status Reportado: {telemetry.get('status', 'Normal')}\n"
    )

    if not gemini_key:
        fallback_msg = (
            f"👷‍♂️ *Parecer do Especialista Solar (IA)*\n\n"
            f"⚠️ *Nota:* A `GEMINI_API_KEY` não está configurada no `.env` do servidor.\n"
            f"Para receber a análise técnica automatizada por Inteligência Artificial em tempo real, "
            f"insira a sua chave Gemini API no arquivo `.env`."
        )
        print("=== [DRY-RUN] Parecer Especialista IA Sem Chave ===")
        print(fallback_msg)
        return fallback_msg

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": gemini_key
    }
    payload = {
        "contents": [{
            "parts": [
                {"text": SOLAR_EXPERT_SYSTEM_PROMPT},
                {"text": prompt_context}
            ]
        }]
    }

    ai_diagnostic = None
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code == 200:
            res_data = res.json()
            ai_diagnostic = res_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            logging.error(f"Erro na API do Gemini: HTTP {res.status_code} - {res.text}")
    except Exception as e:
        logging.error(f"Exceção ao consultar o Agente Especialista IA (Gemini): {e}")

    if not ai_diagnostic:
        ai_diagnostic = (
            f"👷‍♂️ *Diagnóstico do Especialista Solar*\n\n"
            f"⚠️ Ocorreu uma oscilação na consulta à IA. Se a potência estiver baixa e houver nuvens ou chuva, "
            f"aguarde a estabilização da irradiação solar antes de qualquer intervenção."
        )

    telegram_msg = (
        f"👷‍♂️ *PARECER DO ESPECIALISTA SOLAR (IA)*\n"
        f"📌 *Análise Técnica:* `{anomaly_info.get('title')}`\n\n"
        f"{ai_diagnostic}"
    )

    if dry_run:
        print("=== [DRY-RUN] Diagnóstico do Especialista Solar (IA) ===")
        print(telegram_msg)
        return telegram_msg

    if tg_token and tg_user_id:
        try:
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={"chat_id": tg_user_id, "text": telegram_msg, "parse_mode": "Markdown"},
                timeout=10
            )
            logging.info("✅ Diagnóstico do Especialista Solar (IA) enviado com sucesso para o Telegram!")
        except Exception as etg:
            logging.error(f"Erro ao enviar diagnóstico da IA no Telegram: {etg}")

    return telegram_msg

if __name__ == "__main__":
    test_anomaly = {
        "key": "pv_string_fault",
        "title": "Queda / Desconexão na String PV2",
        "detail": "Tensão PV1: 125.0 V | Tensão PV2: 4.2 V (Anormal em pico sol)"
    }
    test_telemetry = {
        "timestamp": datetime.now(BR_TZ).isoformat(),
        "power_w": 950.0,
        "today_kwh": 6.4,
        "temperature": 41.2,
        "pv1_voltage": 125.0,
        "pv1_current": 7.6,
        "pv2_voltage": 4.2,
        "pv2_current": 0.0,
        "grid_voltage": 224.5,
        "grid_current": 4.2,
        "grid_frequency": 60.0,
        "status": "Normal"
    }
    analyze_solar_anomaly_with_ai(test_anomaly, test_telemetry, dry_run=True)
