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
                        if (
                            "status: ok" in lower_line 
                            or "0 error(s)" in lower_line 
                            or "iniciando monitoramento de logs" in lower_line
                            or "erros consolidados" in lower_line
                            or "solicitando resumo à ia" in lower_line
                            or "nenhum erro crítico" in lower_line
                            or "enviando status ok" in lower_line
                            or "enviando relatório via telegram" in lower_line
                            or "guardrail acionado" in lower_line
                            or ("erro no ciclo: db error" in lower_line and "tests" in file_path)
                        ):
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

def get_weather_and_solar_context():
    """Busca o contexto de meteorologia e geração solar diária para informar o agente IA."""
    try:
        from scripts.solar_forecast import fetch_solar_forecast
    except ImportError:
        try:
            from solar_forecast import fetch_solar_forecast
        except ImportError:
            fetch_solar_forecast = None

    context = {
        "condition": "Desconhecido",
        "estimated_kwh": 0.0,
        "is_solar_window": False,
        "detail": "Sem dados de previsão"
    }

    sp_tz = timezone(timedelta(hours=-3))
    now = datetime.now(sp_tz)
    hour = now.hour

    # Janela solar diurna aproximada: entre 06:30 e 18:30 BRT
    is_solar_window = 6 <= hour < 18 or (hour == 6 and now.minute >= 30) or (hour == 18 and now.minute <= 30)
    context["is_solar_window"] = is_solar_window

    if fetch_solar_forecast:
        try:
            forecast = fetch_solar_forecast()
            if forecast and "today" in forecast:
                today_info = forecast["today"]
                context["condition"] = today_info.get("condition_full", today_info.get("condition", "N/A"))
                context["estimated_kwh"] = today_info.get("estimated_kwh", 0.0)
                context["detail"] = f"Clima Hoje: {context['condition']} | Geração Estimada: {context['estimated_kwh']} kWh"
        except Exception as e:
            print(f"Aviso: Erro ao buscar dados meteorológicos para log_analyzer: {e}")

    return context

def get_ai_summary(errors, weather_ctx=None):
    """Envia os erros para a API do Gemini e obtém o resumo."""
    if not GEMINI_API_KEY:
        print("Aviso: GEMINI_API_KEY não configurada. Usando fallback de resumo em texto.")
        return None
        
    # Formata a lista de erros para mandar para a IA
    error_list_text = ""
    for (service, _), data in errors.items():
        error_list_text += f"- [{service.upper()}] (Ocorreu {data['count']} vez(es)): {data['original']}\n"
        
    weather_text = ""
    if weather_ctx:
        weather_text = (
            f"Contexto Operacional e Meteorológico Atual:\n"
            f"- Janela Solar Diurna Ativa: {'SIM' if weather_ctx.get('is_solar_window') else 'NÃO (Horário Noturno / Pós-pôr do sol)'}\n"
            f"- Clima Registrado Hoje: {weather_ctx.get('condition', 'N/A')}\n"
            f"- Geração Solar Estimada: {weather_ctx.get('estimated_kwh', 0.0)} kWh\n"
            f"- Nota Técnica Guardrail: Inversores solares LAN (192.168.1.13) são energizados pela tensão DC dos painéis. "
            f"Em horários sem sol ou durante chuva densa, o inversor desliga seu servidor Web HTTP (retornando HTTP 404, 503, Timeout ou Conexão Recusada). "
            f"ISSO É COMPORTAMENTO FÍSICO NORMAL DE STANDBY E NÃO DEVE SER CLASSIFICADO COMO ALERTA OU FALHA DE SISTEMA.\n\n"
        )

    prompt = (
        "Você é um engenheiro SRE especialista em Linux e IoT (Raspberry Pi, MQTT, FastAPI). "
        "Analise a lista de erros abaixo vindos dos logs de um sistema doméstico inteligente de iluminação (Light Manager) "
        "e gere um relatório resumido e direto em português (pt-br).\n\n"
        f"{weather_text}"
        "Regras:\n"
        "1. Seja extremamente conciso. Use bullet points.\n"
        "2. Identifique a provável causa raiz (ex: queda de rede, problema no banco postgres, erro no bot).\n"
        "3. Dê uma estimativa de impacto/urgência (Ex: CRÍTICO, ALERTA ou INFORMATIVO).\n"
        "4. Não classifique desconexão/HTTP 404 do inversor solar fora do horário de sol ou durante chuva como erro/ALERTA SRE.\n"
        "5. Não use jargões desnecessários nem introduções longas.\n\n"
        "Lista de Erros:\n"
        f"{error_list_text}"
    )
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }
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
    """Envia uma mensagem de texto pelo bot do Telegram com tratamento de Rate-Limiting."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Erro: TELEGRAM_BOT_TOKEN ou TELEGRAM_ALLOWED_USER_ID não configurados.")
        return False
        
    import time
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    for attempt in range(3):
        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                return True
            elif res.status_code == 429:
                try:
                    retry_after = res.json().get("parameters", {}).get("retry_after", 5)
                except Exception:
                    retry_after = 5
                print(f"Aviso: Rate Limit (429) no Telegram. Aguardando {retry_after}s antes de tentar novamente...")
                time.sleep(retry_after)
            else:
                print(f"Erro ao enviar mensagem no Telegram: HTTP {res.status_code} - {res.text}")
                return False
        except Exception as e:
            print(f"Exceção ao enviar mensagem no Telegram (tentativa {attempt + 1}/3): {e}")
            time.sleep(2)
            
    return False

def main():
    sp_tz = timezone(timedelta(hours=-3))
    now = datetime.now(sp_tz)
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando monitoramento de logs diários...")
    
    errors = extract_errors()
    weather_ctx = get_weather_and_solar_context()
    
    # Define se os erros encontrados são críticos ou comprometem o funcionamento
    critical_errors = {}
    for key, data in errors.items():
        service, normalized = key
        norm_lower = normalized.lower()

        # Ignora avisos leves, por exemplo, conexões do uvicorn normais que foram marcadas com erros secundários
        # ou problemas triviais de download de sol
        if "sun data unavailable" in norm_lower or "ping statistics" in norm_lower:
            continue

        # GUARDRAIL SOLAR & METEOROLÓGICO:
        # Se for log do componente solar indicando erro HTTP 404, file not found, standby ou desconexão:
        is_solar_standby = any(pat in norm_lower for pat in [
            "http 404", "404", "file not found", "connection refused", 
            "timeout", "inacessível (sem sol)", "standby", "offline"
        ])
        if service == "solar" and is_solar_standby:
            is_rainy = any(cond in weather_ctx.get("condition", "").lower() for cond in ["chuva", "chuvisco", "tempestade", "nublado"])
            # Se estiver fora do horário de pico diurno, ou clima chuvoso/sem radiação, ignora falso alarme
            if not weather_ctx.get("is_solar_window") or is_rainy or weather_ctx.get("estimated_kwh", 0) < 1.0:
                print(f"Guardrail acionado: Ignorando log de standby/ausência de sol do inversor ({normalized[:80]}...)")
                continue

        critical_errors[key] = data

    if not critical_errors:
        message = "🤖 <b>Status Light Manager</b>: Tudo OK.\nNenhum erro crítico detectado nas últimas 24h."
        print("Nenhum erro crítico detectado. Enviando status OK.")
        send_telegram_message(message)
        return
        
    print(f"Detectados {len(critical_errors)} tipos de erros consolidados. Solicitando resumo à IA...")
    
    # Tenta obter o resumo da IA
    ai_summary = get_ai_summary(critical_errors, weather_ctx=weather_ctx)
    
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
