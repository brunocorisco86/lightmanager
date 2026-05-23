#!/bin/bash
# scripts/network_watchdog.sh
# Verifica se o Wemos está vivo na rede e se está comunicando via MQTT.
# Se estiver na rede (Ping OK) mas sem enviar Heartbeat, força um Reboot.

PROJECT_ROOT="/home/bruno/lightmanager"
source "$PROJECT_ROOT/.env"

WEMOS_IP=${WEMOS_IP:-"192.168.1.111"}
MQTT_HOST=${MQTT_BROKER:-"localhost"}
MQTT_USER=${MQTT_USER:-"bruno"}
MQTT_PASS=${MQTT_PASSWORD:-"blurbang"}
LOG_FILE="$PROJECT_ROOT/logs/watchdog.log"

echo "[$(date)] 🔍 Watchdog: Verificando Wemos em $WEMOS_IP..." >> "$LOG_FILE"

# 1. Tenta pingar o Wemos
if ping -c 3 -W 2 "$WEMOS_IP" > /dev/null; then
    echo "[$(date)] ✅ Wemos responde ao PING (Rede OK)." >> "$LOG_FILE"
    
    # 2. Verifica se houve heartbeat recente no banco de dados (últimos 5 minutos)
    # Nota: Requer psql instalado. Caso prefira via log, a lógica muda.
    DB_LAST_HB=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT count(*) FROM light_events WHERE timestamp > now() - interval '5 minutes';" | xargs)

    if [ "$DB_LAST_HB" -eq "0" ]; then
        echo "[$(date)] ⚠️  Sem eventos no DB nos últimos 5 min. Enviando REBOOT via MQTT..." >> "$LOG_FILE"
        mosquitto_pub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "home/outdoor/system/reboot" -m "REBOOT"
    else
        echo "[$(date)] ✨ MQTT parece saudável (Eventos detectados)." >> "$LOG_FILE"
    fi
else
    echo "[$(date)] ❌ ERRO: Wemos NAO responde ao PING. Possível queda de WiFi ou Energia." >> "$LOG_FILE"
fi
