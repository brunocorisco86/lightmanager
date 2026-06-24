#!/bin/bash
# scripts/08_flash_wemos.sh
# Grava o firmware atualizado na placa e roda testes de integridade locais, registrando tudo em logs.

# Definir raiz do projeto independentemente de onde o script é chamado
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
cd "$PROJECT_ROOT"

PORT="/dev/ttyUSB0"
BAUD="460800"
BIN_PATH="firmware/wemos_light/wemos_light.bin"
WEMOS_IP="192.168.1.111"
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/flash_wemos.log"

# Garante que a pasta de logs existe
mkdir -p "$LOG_DIR"

# Configurações do Broker MQTT
MQTT_HOST="192.168.1.7"
MQTT_USER="bruno"
MQTT_PASS="blurbang"
SET_TOPIC="home/outdoor/frente/set"
STATE_TOPIC="home/outdoor/frente/state"

# Função utilitária para registrar logs na tela e no arquivo de log
log_msg() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Inicializa o arquivo de log com cabeçalho
echo "========================================================" > "$LOG_FILE"
echo "📝 Log de Flash & Testes do Wemos - $(date)" >> "$LOG_FILE"
echo "========================================================" >> "$LOG_FILE"

log_msg "=== 🔌 Iniciando Script de Flash Wemos D1 ==="

# 1. Verifica se o arquivo binário existe
if [ ! -f "$BIN_PATH" ]; then
    log_msg "❌ Erro: Arquivo binário não encontrado em: $BIN_PATH"
    log_msg "Por favor, compile o código primeiro com 'arduino-cli compile'."
    exit 1
fi

# 2. Verifica se a porta serial existe
if [ ! -e "$PORT" ]; then
    log_msg "❌ Erro: Dispositivo serial $PORT não encontrado!"
    log_msg "Verifique se a placa Wemos D1 está conectada via USB."
    exit 1
fi

# 3. Localiza o esptool
ESPTOOL=$(which esptool 2>/dev/null || which esptool.py 2>/dev/null || echo "$HOME/.local/bin/esptool")
if [ ! -f "$ESPTOOL" ] && [ ! -x "$(command -v esptool)" ] && [ ! -x "$(command -v esptool.py)" ]; then
    log_msg "❌ Erro: 'esptool' não encontrado! Instale-o com: pip install esptool"
    exit 1
fi

log_msg "✅ Arquivos e porta serial localizados."

# 4. Identificação do Hardware
log_msg "\n=== 🔍 Identificando o Hardware Conectado ==="
BOARD_INFO=$("$ESPTOOL" --port "$PORT" flash_id 2>&1)
echo "$BOARD_INFO" >> "$LOG_FILE"

CHIP_TYPE=$(echo "$BOARD_INFO" | grep -i "Detecting chip type" | awk -F': ' '{print $2}')
FLASH_SIZE=$(echo "$BOARD_INFO" | grep -i "Detected flash size" | awk -F': ' '{print $2}')
log_msg "Placa Detectada: Chip=${CHIP_TYPE:-ESP8266}, Flash Size=${FLASH_SIZE:-Desconhecida}"

# 5. Conferir no código se o binário está adequado para a placa
log_msg "\n=== 🔍 Validando Compatibilidade do Binário ==="
IMAGE_INFO=$("$ESPTOOL" image_info "$BIN_PATH" 2>&1)
echo "$IMAGE_INFO" >> "$LOG_FILE"

# Extrai o Target Chip do binário
BIN_CHIP=$(echo "$IMAGE_INFO" | grep -i "Target chip" | awk -F': ' '{print $2}' | tr -d '[:space:]')
if [ -z "$BIN_CHIP" ]; then
    # Tratamento alternativo para versões do esptool que mostram de forma simplificada
    if echo "$IMAGE_INFO" | grep -q "ESP8266"; then
        BIN_CHIP="ESP8266"
    fi
fi

log_msg "Binário compilado para: ${BIN_CHIP:-Desconhecido}"

if [ "$BIN_CHIP" != "ESP8266" ]; then
    log_msg "❌ Erro: O binário compilado não é adequado para esta placa (esperado: ESP8266, obtido: $BIN_CHIP)!"
    exit 1
fi
log_msg "✅ Compatibilidade validada com sucesso."

# 6. Executa a gravação e gera logs
log_msg "\n=== ⚡ Gravando Firmware via esptool ==="
log_msg "⚡ Gravando $BIN_PATH em $PORT na velocidade de $BAUD baud..."
"$ESPTOOL" --port "$PORT" --baud "$BAUD" write-flash 0x0 "$BIN_PATH" 2>&1 | tee -a "$LOG_FILE"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log_msg "\n✅ Gravação concluída com sucesso!"
    log_msg "⏳ Aguardando 7 segundos para a placa inicializar e conectar ao Wi-Fi..."
    sleep 7

    # 7. Validação de rede (Ping) e geração de logs
    log_msg "\n=== 🔍 Iniciando Testes Pós-Flash ==="
    log_msg "🔍 Verificando conectividade de rede com o IP $WEMOS_IP..."
    ping -c 3 -W 2 "$WEMOS_IP" 2>&1 | tee -a "$LOG_FILE"
    
    if ping -c 3 -W 2 "$WEMOS_IP" > /dev/null; then
        log_msg "✅ Sucesso! O dispositivo Wemos D1 está online e respondendo a pings."
        log_msg ""

        # 8. Validação do Broker MQTT e logs
        log_msg "🔍 Iniciando teste de comunicação via Broker MQTT..."
        
        MQTT_OUT=$(mktemp)
        
        timeout 6s mosquitto_sub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$STATE_TOPIC" -v > "$MQTT_OUT" &
        SUB_PID=$!
        
        sleep 1.5
        
        log_msg "💡 [PC -> Broker] Enviando comando 'ON' para $SET_TOPIC..."
        mosquitto_pub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$SET_TOPIC" -m "ON" 2>&1 | tee -a "$LOG_FILE"
        sleep 1.5
        
        log_msg "🔌 [PC -> Broker] Enviando comando 'OFF' para $SET_TOPIC..."
        mosquitto_pub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$SET_TOPIC" -m "OFF" 2>&1 | tee -a "$LOG_FILE"
        sleep 1.5
        
        wait $SUB_PID 2>/dev/null
        
        log_msg "=== 📨 Respostas (ACK) recebidas da placa pelo Broker ==="
        cat "$MQTT_OUT" | tee -a "$LOG_FILE"
        log_msg "========================================================"
        
        ACK_ON=$(grep -c "ON" "$MQTT_OUT")
        ACK_OFF=$(grep -c "OFF" "$MQTT_OUT")
        
        rm -f "$MQTT_OUT"
        
        if [ "$ACK_ON" -gt 0 ] && [ "$ACK_OFF" -gt 0 ]; then
            log_msg "✅ SIMULAÇÃO MQTT OK! A placa processou os comandos e enviou os devidos ACKs."
            log_msg "\n🎉 Processo de Flash e Validação concluído com absoluto sucesso!"
        else
            log_msg "❌ ERRO DE COMUNICAÇÃO: A placa não enviou os ACKs esperados de ON/OFF pelo broker."
            exit 1
        fi
    else
        log_msg "⚠️ Alerta: Gravação concluída, mas o dispositivo não respondeu ao ping no IP $WEMOS_IP."
        log_msg "Verifique as credenciais do Wi-Fi no código."
        exit 1
    fi
else
    log_msg "❌ Erro: Falha na gravação do firmware!"
    exit 1
fi
