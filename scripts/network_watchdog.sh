#!/bin/bash
# scripts/network_watchdog.sh
# Verifica se o Wemos está vivo na rede e se está comunicando via MQTT.
# Se estiver na rede (Ping OK) mas sem enviar Heartbeat (arquivo local), força um Reboot.

PROJECT_ROOT="/home/bruno/lightmanager"
source "$PROJECT_ROOT/.env"

WEMOS_IP=${WEMOS_IP:-"192.168.1.111"}
MQTT_HOST=${MQTT_BROKER:-"localhost"}
MQTT_USER=${MQTT_USER:-"bruno"}
MQTT_PASS=${MQTT_PASSWORD:-"blurbang"}
LOG_FILE="$PROJECT_ROOT/logs/watchdog.log"
LAST_SEEN_FILE="/tmp/wemos_last_seen"

echo "[$(date)] 🔍 Watchdog: Verificando Wemos em $WEMOS_IP..." >> "$LOG_FILE"

# 1. Tenta pingar o Wemos
if ping -c 3 -W 2 "$WEMOS_IP" > /dev/null; then
    echo "[$(date)] ✅ Wemos responde ao PING (Rede OK)." >> "$LOG_FILE"
    
    # 2. Verifica a última atividade (arquivo local atualizado pelo solar_worker)
    # Evita consultas constantes ao PostgreSQL.
    if [ -f "$LAST_SEEN_FILE" ]; then
        LAST_SEEN_TS=$(cat "$LAST_SEEN_FILE")
        CURRENT_TS=$(date +%s)
        DIFF=$((CURRENT_TS - ${LAST_SEEN_TS%.*})) # Remove decimais se houver

        if [ "$DIFF" -gt 600 ]; then # 10 minutos (Wemos envia status a cada 60s)
            echo "[$(date)] ⚠️  Sem atividade MQTT há $DIFF segundos. Enviando REBOOT via MQTT..." >> "$LOG_FILE"
            mosquitto_pub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "home/outdoor/system/reboot" -m "REBOOT"
        else
            echo "[$(date)] ✨ MQTT saudável (Última atividade há $DIFF segundos)." >> "$LOG_FILE"
        fi
    else
        echo "[$(date)] ⏳ Arquivo heartbeat não encontrado. Aguardando primeira comunicação..." >> "$LOG_FILE"
    fi
else
    echo "[$(date)] ❌ ERRO: Wemos NAO responde ao PING. Possível queda de WiFi ou Energia." >> "$LOG_FILE"
fi
