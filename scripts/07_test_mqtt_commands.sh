#!/bin/bash
# scripts/07_test_mqtt_commands.sh

BROKER="192.168.1.7"
USER="bruno"
PASS="blurbang"

# Função para enviar comando
send_cmd() {
    local topic=$1
    local payload=$2
    echo "➡ Enviando $payload para $topic..."
    mosquitto_pub -h $BROKER -u $USER -P $PASS -t "$topic" -m "$payload"
}

echo "=== Iniciando Teste de Acionamento MQTT ==="

# Sequência de teste para Frente
send_cmd "home/outdoor/frente/set" "ON"
sleep 2
send_cmd "home/outdoor/frente/set" "OFF"

# Sequência de teste para Fundos
send_cmd "home/outdoor/fundos/set" "ON"
sleep 2
send_cmd "home/outdoor/fundos/set" "OFF"

echo "=== Teste finalizado ==="
