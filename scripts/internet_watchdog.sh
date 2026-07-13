#!/bin/bash
# scripts/internet_watchdog.sh
# Verifica a conectividade com a internet e resolve falhas locais do servidor Unbound DNS.

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
    # Tudo perfeito
    if [ "$FAIL_COUNT" -ne 0 ]; then
        echo "[$(date)] 🌐 Conectividade geral restabelecida. Resetando falhas." >> "$LOG_FILE"
        echo "0" > "$FAIL_COUNT_FILE"
    fi
elif [ "$ping_ok" -eq 1 ] && [ "$dns_ok" -eq 0 ]; then
    # Ping funciona mas DNS falhou (Unbound local travado)
    echo "[$(date)] ⚠️  Alerta: Ping externo OK, mas resolução de nomes DNS local falhou. Culpado provável: Unbound local." >> "$LOG_FILE"
    echo "[$(date)] 🔄 Reiniciando serviço unbound local..." >> "$LOG_FILE"
    sudo rc-service unbound restart >> "$LOG_FILE" 2>&1
    sleep 3
    
    # Retesta o DNS
    if nslookup "$TEST_HOST" > /dev/null 2>&1; then
        echo "[$(date)] ✅ Unbound recuperado com sucesso. Resolução de DNS restabelecida." >> "$LOG_FILE"
        echo "0" > "$FAIL_COUNT_FILE"
    else
        echo "[$(date)] ❌ Falha crítica: Unbound reiniciado mas DNS continua inoperante." >> "$LOG_FILE"
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
        sudo rc-service unbound restart >> "$LOG_FILE" 2>&1
    fi
fi
