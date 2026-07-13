#!/usr/bin/env python3
# scripts/log_analyzer.py
# Script de monitoramento e análise de logs com IA (Gemini) e envio via Telegram.

import os
import re
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Configura caminhos e carrega o .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(BASE_DIR, '..')
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

# Configurações de chaves e variáveis do .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")

LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
LOG_FILES = {
    "api": os.path.join(LOGS_DIR, "api.log"),
    "bot": os.path.join(LOGS_DIR, "bot.log"),
    "solar": os.path.join(LOGS_DIR, "solar.log"),
    "cron": os.path.join(LOGS_DIR, "cron.log"),
    "watchdog": os.path.join(LOGS_DIR, "watchdog.log"),
    "backup": os.path.join(LOGS_DIR, "backup.log"),
    "devices": os.path.join(LOGS_DIR, "devices.log"),
    "broker": "/var/log/mosquitto/mosquitto.log"
}

# Palavras-chave de erro
ERROR_KEYWORDS = ["error", "fail", "erro", "exception", "traceback", "failed", "operationalerror", "dnserror"]

# Expressões regulares para remover timestamps comuns na normalização
TIMESTAMP_REGEXES = [
    re.compile(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}[,.]\d{3}'), # 2026-07-12 22:01:47,898
    re.compile(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}'),          # 2026-07-12 22:01:47
    re.compile(r'\[[A-Za-z]{3} [A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2} [^\]]+\]'), # [Sun Jul 12 22:00:49 -03 2026]
    re.compile(r'\b\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\b')          # 2026/07/12 22:01:47
]

def clean_timestamp(line):
    """Remove timestamps e datas da linha para agrupar erros repetidos."""
    for regex in TIMESTAMP_REGEXES:
        line = regex.sub('', line)
    return line.strip()

def extract_errors():
    """Lê todos os logs e extrai erros consolidados desduplicados."""
    consolidated_errors = {}
    
    for service, file_path in LOG_FILES.items():
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    lower_line = line.lower()
                    if any(kw in lower_line for kw in ERROR_KEYWORDS):
                        # Ignora logs de info que contêm a palavra erro mas não são erros
                        if "status: ok" in lower_line or "0 error(s)" in lower_line or "erro no ciclo: db error" in lower_line and "tests" in file_path:
                            continue
                            
                        normalized = clean_timestamp(line)
                        # Remove PID e dados dinâmicos como IPs de uvicorn/logs
                        normalized = re.sub(r'\[\d+\]', '[PID]', normalized) # [4004] -> [PID]
                        normalized = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b', '[ADDRESS]', normalized) # 192.168.1.90:40752 -> [ADDRESS]
                        
                        key = (service, normalized)
                        if key not in consolidated_errors:
                            consolidated_errors[key] = {
                                "original": line.strip(),
                                "count": 1
                            }
                        else:
                            consolidated_errors[key]["count"] += 1
        except Exception as e:
            print(f"Erro ao ler log {service}: {e}")
            
    return consolidated_errors

def get_ai_summary(errors):
    """Envia os erros para a API do Gemini e obtém o resumo."""
    if not GEMINI_API_KEY:
        print("Aviso: GEMINI_API_KEY não configurada. Usando fallback de resumo em texto.")
        return None
        
    # Formata a lista de erros para mandar para a IA
    error_list_text = ""
    for (service, _), data in errors.items():
        error_list_text += f"- [{service.upper()}] (Ocorreu {data['count']} vez(es)): {data['original']}\n"
        
    prompt = (
        "Você é um engenheiro SRE especialista em Linux e IoT (Raspberry Pi, MQTT, FastAPI). "
        "Analise a lista de erros abaixo vindos dos logs de um sistema doméstico inteligente de iluminação (Light Manager) "
        "e gere um relatório resumido e direto em português (pt-br).\n\n"
        "Regras:\n"
        "1. Seja extremamente conciso. Use bullet points.\n"
        "2. Identifique a provável causa raiz (ex: queda de rede, problema no banco postgres, erro no bot).\n"
        "3. Dê uma estimativa de impacto/urgência (Ex: CRÍTICO, ALERTA ou INFORMATIVO).\n"
        "4. Não use jargões desnecessários nem introduções longas.\n\n"
        "Lista de Erros:\n"
        f"{error_list_text}"
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            print(f"Aviso: Não foi possível obter resumo da IA (HTTP {res.status_code}). Usando fallback de resumo em texto simples.")
    except Exception as e:
        print(f"Aviso: Exceção ao chamar a API do Gemini: {e}. Usando fallback de resumo em texto simples.")
        
    return None

def send_telegram_message(text):
    """Envia uma mensagem de texto pelo bot do Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Erro: TELEGRAM_BOT_TOKEN ou TELEGRAM_ALLOWED_USER_ID não configurados.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"Erro ao enviar mensagem no Telegram: {e}")
        return False

def main():
    sp_tz = timezone(timedelta(hours=-3))
    now = datetime.now(sp_tz)
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando monitoramento de logs diários...")
    
    errors = extract_errors()
    
    # Define se os erros encontrados são críticos ou comprometem o funcionamento
    critical_errors = {}
    for key, data in errors.items():
        service, normalized = key
        # Ignora avisos leves, por exemplo, conexões do uvicorn normais que foram marcadas com erros secundários
        # ou problemas triviais de download de sol
        if "sun data unavailable" in normalized.lower() or "ping statistics" in normalized.lower():
            continue
        critical_errors[key] = data

    if not critical_errors:
        message = "🤖 <b>Status Light Manager</b>: Tudo OK.\nNenhum erro crítico detectado nas últimas 24h."
        print("Nenhum erro crítico detectado. Enviando status OK.")
        send_telegram_message(message)
        return
        
    print(f"Detectados {len(critical_errors)} tipos de erros consolidados. Solicitando resumo à IA...")
    
    # Tenta obter o resumo da IA
    ai_summary = get_ai_summary(critical_errors)
    
    if ai_summary:
        message = (
            f"⚠️ <b>Relatório Diário de Erros - Light Manager</b>\n"
            f"Data: {now.strftime('%d/%m/%Y %H:%M')}\n\n"
            f"{ai_summary}"
        )
    else:
        # Fallback de texto se a IA falhar
        fallback_text = "⚠️ <b>Relatório Diário de Erros (Fallback)</b>\n"
        fallback_text += f"Data: {now.strftime('%d/%m/%Y %H:%M')}\n\n"
        fallback_text += "A API da IA não respondeu. Segue a lista bruta de erros desduplicados:\n\n"
        for (service, _), data in critical_errors.items():
            fallback_text += f"• <b>[{service.upper()}]</b> (ocorrências: {data['count']})\n<code>{data['original'][:120]}...</code>\n\n"
        message = fallback_text
        
    print("Enviando relatório via Telegram...")
    send_telegram_message(message)

if __name__ == "__main__":
    main()
