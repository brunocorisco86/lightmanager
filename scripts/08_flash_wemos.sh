#!/bin/bash
# scripts/08_flash_wemos.sh

# Definir raiz do projeto independentemente de onde o script é chamado
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
cd "$PROJECT_ROOT"

PORT="/dev/ttyUSB0"
BAUD="460800"
BIN_PATH="firmware/wemos_light/wemos_light.bin"
WEMOS_IP="192.168.1.111"

# Configurações do Broker MQTT
MQTT_HOST="192.168.1.7"
MQTT_USER="bruno"
MQTT_PASS="blurbang"
SET_TOPIC="home/outdoor/frente/set"
STATE_TOPIC="home/outdoor/frente/state"

echo "=== 🔌 Iniciando Script de Flash Wemos D1 ==="

# 1. Verifica se o arquivo binário existe
if [ ! -f "$BIN_PATH" ]; then
    echo "❌ Erro: Arquivo binário não encontrado em: $BIN_PATH"
    echo "Por favor, compile o código no Arduino IDE primeiro."
    exit 1
fi

# 2. Verifica se a porta serial existe
if [ ! -e "$PORT" ]; then
    echo "❌ Erro: Dispositivo serial $PORT não encontrado!"
    echo "Verifique se a placa Wemos D1 está conectada via USB."
    exit 1
fi

# 3. Localiza o esptool
ESPTOOL=$(which esptool 2>/dev/null || which esptool.py 2>/dev/null || echo "$HOME/.local/bin/esptool")
if [ ! -f "$ESPTOOL" ] && [ ! -x "$(command -v esptool)" ] && [ ! -x "$(command -v esptool.py)" ]; then
    echo "❌ Erro: 'esptool' não encontrado! Instale-o com: pip install esptool"
    exit 1
fi

echo "✅ Arquivos e porta serial localizados."
echo "⚡ Gravando $BIN_PATH em $PORT na velocidade de $BAUD baud..."

# 4. Executa a gravação
"$ESPTOOL" --port "$PORT" --baud "$BAUD" write-flash 0x0 "$BIN_PATH"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Gravação concluída com sucesso!"
    echo "⏳ Aguardando 7 segundos para a placa inicializar e conectar ao Wi-Fi..."
    sleep 7

    # 5. Validação de rede (Ping)
    echo "🔍 Verificando conectividade de rede com o IP $WEMOS_IP..."
    if ping -c 3 -W 2 "$WEMOS_IP" > /dev/null; then
        echo "✅ Sucesso! O dispositivo Wemos D1 está online e respondendo a pings."
        echo ""

        # 6. Validação do Broker MQTT e simulação de comando/ACK
        echo "🔍 Iniciando teste de comunicação via Broker MQTT..."
        
        # Cria arquivo temporário para capturar o ACK da placa
        MQTT_OUT=$(mktemp)
        
        # Subscreve em background no tópico de estado para capturar as respostas
        timeout 6s mosquitto_sub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$STATE_TOPIC" -v > "$MQTT_OUT" &
        SUB_PID=$!
        
        # Dá tempo para o subscriber iniciar a escuta
        sleep 1.5
        
        # Envia comando ON
        echo "💡 [PC -> Broker] Enviando comando 'ON' para $SET_TOPIC..."
        mosquitto_pub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$SET_TOPIC" -m "ON"
        sleep 1.5
        
        # Envia comando OFF
        echo "🔌 [PC -> Broker] Enviando comando 'OFF' para $SET_TOPIC..."
        mosquitto_pub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$SET_TOPIC" -m "OFF"
        sleep 1.5
        
        # Espera o subscriber finalizar (encerrado pelo timeout interno de 6s)
        wait $SUB_PID 2>/dev/null
        
        echo "=== 📨 Respostas (ACK) recebidas da placa pelo Broker ==="
        cat "$MQTT_OUT"
        echo "========================================================"
        
        # Valida se recebemos os estados corretos de volta
        ACK_ON=$(grep -c "ON" "$MQTT_OUT")
        ACK_OFF=$(grep -c "OFF" "$MQTT_OUT")
        
        # Limpa arquivo temporário
        rm -f "$MQTT_OUT"
        
        if [ "$ACK_ON" -gt 0 ] && [ "$ACK_OFF" -gt 0 ]; then
            echo "✅ SIMULAÇÃO MQTT OK! A placa processou os comandos e enviou os devidos ACKs."
        else
            echo "❌ ERRO DE COMUNICAÇÃO: A placa não enviou os ACKs esperados de ON/OFF pelo broker."
            exit 1
        fi
    else
        echo "⚠️ Alerta: Gravação concluída, mas o dispositivo não respondeu ao ping no IP $WEMOS_IP."
        echo "Verifique as credenciais do Wi-Fi no código."
        exit 1
    fi
else
    echo "❌ Erro: Falha na gravação do firmware!"
    exit 1
fi
