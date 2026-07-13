#!/bin/bash
# scripts/internet_watchdog.sh
# Verifica a conectividade com a internet e resolve falhas locais do servidor Unbound DNS com governança de reinício.

DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
LOG_FILE="$PROJECT_ROOT/logs/watchdog.log"
FAIL_COUNT_FILE="/tmp/internet_fail_count"
UNBOUND_FAIL_FILE="/tmp/unbound_restart_count"

# Carrega as variáveis do .env do projeto
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
fi

# IPs e hosts para testar
TEST_IP1="8.8.8.8"
TEST_IP2="1.1.1.1"
TEST_HOST="api.telegram.org"

# Inicializa contadores se não existirem
if [ ! -f "$FAIL_COUNT_FILE" ]; then
    echo "0" > "$FAIL_COUNT_FILE"
fi
if [ ! -f "$UNBOUND_FAIL_FILE" ]; then
    echo "0" > "$UNBOUND_FAIL_FILE"
fi

FAIL_COUNT=$(cat "$FAIL_COUNT_FILE")
UNBOUND_RESTARTS=$(cat "$UNBOUND_FAIL_FILE")

# Função para enviar alerta via Telegram
send_telegram_alert() {
    local text="$1"
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_ALLOWED_USER_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\": \"${TELEGRAM_ALLOWED_USER_ID}\", \"text\": \"${text}\", \"parse_mode\": \"Markdown\"}" > /dev/null
    fi
}

# Testa ping físico nos servidores DNS públicos
ping_ok=0
if ping -c 2 -W 2 "$TEST_IP1" > /dev/null 2>&1 || ping -c 2 -W 2 "$TEST_IP2" > /dev/null 2>&1; then
    ping_ok=1
fi

# Testa resolução de nomes DNS do sistema
dns_ok=0
if nslookup "$TEST_HOST" > /dev/null 2>&1; then
    dns_ok=1
fi

if [ "$ping_ok" -eq 1 ] && [ "$dns_ok" -eq 1 ]; then
    # Tudo perfeito - Reseta todos os contadores de falha
    if [ "$FAIL_COUNT" -ne 0 ] || [ "$UNBOUND_RESTARTS" -ne 0 ]; then
        echo "[$(date)] 🌐 Conectividade geral e DNS restabelecidos. Resetando contadores." >> "$LOG_FILE"
        echo "0" > "$FAIL_COUNT_FILE"
        echo "0" > "$UNBOUND_FAIL_FILE"
    fi
elif [ "$ping_ok" -eq 1 ] && [ "$dns_ok" -eq 0 ]; then
    # Ping funciona mas DNS falhou (Unbound local travado)
    echo "[$(date)] ⚠️  Alerta: Ping externo OK, mas resolução de nomes DNS local falhou. Culpado provável: Unbound local." >> "$LOG_FILE"
    
    if [ "$UNBOUND_RESTARTS" -lt 1 ]; then
        UNBOUND_RESTARTS=$((UNBOUND_RESTARTS + 1))
        echo "$UNBOUND_RESTARTS" > "$UNBOUND_FAIL_FILE"
        echo "[$(date)] 🔄 Reiniciando serviço unbound local (Tentativa de autorrecuperação $UNBOUND_RESTARTS de 1)..." >> "$LOG_FILE"
        
        sudo rc-service unbound restart >> "$LOG_FILE" 2>&1
        sleep 3
        
        # Retesta o DNS
        if nslookup "$TEST_HOST" > /dev/null 2>&1; then
            echo "[$(date)] ✅ Unbound recuperado com sucesso. Resolução de DNS restabelecida." >> "$LOG_FILE"
            echo "0" > "$UNBOUND_FAIL_FILE"
        else
            echo "[$(date)] ❌ Falha crítica: Unbound reiniciado mas DNS continua inoperante." >> "$LOG_FILE"
            send_telegram_alert "⚠️ *Alerta SRE*: O DNS local Unbound foi reiniciado automaticamente mas a resolução de nomes continua falhando."
        fi
    else
        # Limite de reinício consecutivo atingido. Evita reinício em excesso.
        echo "[$(date)] ⚠️  Aviso: Unbound inoperante, mas o limite de reinício consecutivo (1) foi atingido. Evitando reinício em excesso para proteger outros serviços." >> "$LOG_FILE"
        
        # Envia apenas uma notificação via Telegram sobre a falha persistente para evitar spam
        if [ "$UNBOUND_RESTARTS" -eq 1 ]; then
            UNBOUND_RESTARTS=$((UNBOUND_RESTARTS + 1))
            echo "$UNBOUND_RESTARTS" > "$UNBOUND_FAIL_FILE"
            send_telegram_alert "🚨 *Alerta SRE*: O DNS local Unbound está travado e o limite de reinício automático foi atingido. Intervenção manual é necessária para evitar instabilidade na rede local."
        fi
    fi
else
    # Queda de conectividade física geral (Ping e DNS falharam)
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "$FAIL_COUNT" > "$FAIL_COUNT_FILE"
    echo "[$(date)] 🌐 Falha geral de conectividade física de rede (Tentativa $FAIL_COUNT de 3)." >> "$LOG_FILE"
    
    if [ "$FAIL_COUNT" -ge 3 ]; then
        echo "[$(date)] 🚨 Rede física inativa por 3 verificações seguidas. Reiniciando interfaces de rede..." >> "$LOG_FILE"
        echo "0" > "$FAIL_COUNT_FILE"
        
        # Tenta reiniciar os serviços de rede do Alpine
        sudo rc-service networking restart >> "$LOG_FILE" 2>&1
        sleep 5
        sudo rc-service wpa_supplicant restart >> "$LOG_FILE" 2>&1
        sleep 5
        # Faz uma única tentativa de reiniciar o unbound também ao recuperar a rede física
        sudo rc-service unbound restart >> "$LOG_FILE" 2>&1
    fi
fi
