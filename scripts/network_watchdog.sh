#!/bin/bash
# scripts/network_watchdog.sh
# Verifica se o Wemos está vivo na rede e se está comunicando via MQTT.
# Se estiver na rede (Ping OK) mas sem enviar Heartbeat (arquivo local), força um Reboot.

# Definir raiz do projeto independentemente de onde o script é chamado
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
cd "$PROJECT_ROOT"

source "$PROJECT_ROOT/.env"

WEMOS_IP=${WEMOS_IP:-"192.168.1.111"}
ESP32_MURO_IP=${ESP32_MURO_IP:-"192.168.1.112"}
MQTT_HOST=${MQTT_BROKER:-"localhost"}
MQTT_USER=${MQTT_USER}
MQTT_PASS=${MQTT_PASSWORD}
LOG_FILE="$PROJECT_ROOT/logs/watchdog.log"

echo "[$(date)] 🔍 Watchdog: Verificando Embarcados (Wemos: $WEMOS_IP | ESP32-C3 Muro: $ESP32_MURO_IP)..." >> "$LOG_FILE"

# 1. Tenta pingar o Wemos (Fachada & Fundos)
if ping -c 3 -W 2 "$WEMOS_IP" > /dev/null; then
    echo "[$(date)] ✅ Wemos ($WEMOS_IP) responde ao PING (Rede OK)." >> "$LOG_FILE"
else
    echo "[$(date)] ❌ ERRO: Wemos ($WEMOS_IP) NAO responde ao PING. Possível queda de WiFi ou Energia." >> "$LOG_FILE"
fi

# 2. Tenta pingar o ESP32-C3 (Muro & Auxiliar)
if ping -c 3 -W 2 "$ESP32_MURO_IP" > /dev/null; then
    echo "[$(date)] ✅ ESP32-C3 Muro ($ESP32_MURO_IP) responde ao PING (Rede OK)." >> "$LOG_FILE"
else
    echo "[$(date)] ⚠️ AVISO: ESP32-C3 Muro ($ESP32_MURO_IP) NAO responde ao PING." >> "$LOG_FILE"
fi

# 3. Verifica a última atividade MQTT de cada embarcado (arquivos atualizados pelo solar_worker)
check_device_activity() {
    local NAME="$1" SEEN_FILE="$2" REBOOT_TOPIC="$3"
    if [ -f "$SEEN_FILE" ]; then
        local LAST_SEEN_TS CURRENT_TS DIFF
        LAST_SEEN_TS=$(cat "$SEEN_FILE")
        CURRENT_TS=$(date +%s)
        DIFF=$((CURRENT_TS - ${LAST_SEEN_TS%.*}))
        if [ "$DIFF" -gt 600 ]; then # 10 minutos
            echo "[$(date)] ⚠️ $NAME sem atividade MQTT há $DIFF segundos. Enviando REBOOT em $REBOOT_TOPIC..." >> "$LOG_FILE"
            mosquitto_pub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$REBOOT_TOPIC" -m "REBOOT"
        else
            echo "[$(date)] ✨ $NAME MQTT saudável (Última atividade há $DIFF segundos)." >> "$LOG_FILE"
        fi
    else
        echo "[$(date)] ⏳ $NAME: arquivo heartbeat não encontrado. Aguardando primeira comunicação..." >> "$LOG_FILE"
    fi
}

check_device_activity "Wemos" "/tmp/wemos_last_seen" "home/outdoor/system/reboot"
check_device_activity "ESP32-C3 Muro" "/tmp/esp32_muro_last_seen" "home/outdoor/muro/reboot"
