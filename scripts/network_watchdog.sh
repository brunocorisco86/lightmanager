#!/bin/bash
# scripts/network_watchdog.sh
# Verifica se o Wemos está vivo e força reboot se necessário

PROJECT_ROOT="/home/bruno/lightmanager"
source "$PROJECT_ROOT/.env"

WEMOS_IP=${WEMOS_IP:-"192.168.1.111"}
MQTT_HOST=${MQTT_BROKER:-"localhost"}
MQTT_USER=${MQTT_USER:-"bruno"}
MQTT_PASS=${MQTT_PASSWORD:-"blurbang"}

echo "[$(date)] Watchdog: Verificando Wemos em $WEMOS_IP..."

# Tenta pingar o Wemos (3 pacotes, espera 2s)
if ping -c 3 -W 2 "$WEMOS_IP" > /dev/null; then
    echo "[$(date)] Wemos responde ao PING (Rede OK)."
else
    echo "[$(date)] ERRO: Wemos NAO responde ao PING. Possível queda de WiFi ou Energia."
    exit 1
fi

# Aqui você poderia adicionar uma lógica para checar o banco de dados
# Se o último evento foi há mais de 10 minutos, força o reboot MQTT
# Por enquanto, vamos apenas deixar o comando pronto:

# mosquitto_pub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "home/outdoor/system/reboot" -m "REBOOT"
