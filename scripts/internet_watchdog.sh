#!/bin/bash
# scripts/internet_watchdog.sh
# Verifica a conectividade com a internet e reinicia a rede do Raspberry Pi se estiver fora do ar.

DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
LOG_FILE="$PROJECT_ROOT/logs/watchdog.log"
FAIL_COUNT_FILE="/tmp/internet_fail_count"

# IPs e hosts para testar
TEST_IP1="8.8.8.8"
TEST_IP2="1.1.1.1"
TEST_HOST="api.telegram.org"

# Inicializa contador se não existir
if [ ! -f "$FAIL_COUNT_FILE" ]; then
    echo "0" > "$FAIL_COUNT_FILE"
fi

FAIL_COUNT=$(cat "$FAIL_COUNT_FILE")

# Função para testar conexão
check_connection() {
    # Tenta pingar IP1
    if ping -c 2 -W 2 "$TEST_IP1" > /dev/null 2>&1; then
        return 0
    fi
    # Tenta pingar IP2
    if ping -c 2 -W 2 "$TEST_IP2" > /dev/null 2>&1; then
        return 0
    fi
    # Tenta resolver DNS do Telegram
    if nslookup "$TEST_HOST" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

if check_connection; then
    # Se a conexão está OK
    if [ "$FAIL_COUNT" -ne 0 ]; then
        echo "[$(date)] 🌐 Internet recuperada. Resetando contador de falhas." >> "$LOG_FILE"
        echo "0" > "$FAIL_COUNT_FILE"
    fi
else
    # Se a conexão falhou
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "$FAIL_COUNT" > "$FAIL_COUNT_FILE"
    echo "[$(date)] 🌐 Falha detectada de internet (Tentativa $FAIL_COUNT de 3)." >> "$LOG_FILE"
    
    if [ "$FAIL_COUNT" -ge 3 ]; then
        echo "[$(date)] 🚨 Internet fora do ar por 3 verificações seguidas. Reiniciando interfaces de rede..." >> "$LOG_FILE"
        echo "0" > "$FAIL_COUNT_FILE"
        
        # Tenta reiniciar os serviços de rede do Alpine
        sudo rc-service networking restart >> "$LOG_FILE" 2>&1
        sleep 5
        sudo rc-service wpa_supplicant restart >> "$LOG_FILE" 2>&1
    fi
fi
