#!/bin/bash
# scripts/09_flash_esp32c3.sh
# Compila e grava o firmware no ESP32-C3 SuperMini, com testes de conectividade pós-flash.

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
cd "$PROJECT_ROOT"

SKETCH_DIR="firmware/esp32c3_radar"
FQBN="esp32:esp32:esp32c3"
BUILD_FLAGS="build.extra_flags=-DARDUINO_USB_MODE=1 -DARDUINO_USB_CDC_ON_BOOT=1"
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/flash_esp32c3.log"
mkdir -p "$LOG_DIR"

log_msg() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

echo "========================================================" > "$LOG_FILE"
echo "📝 Log de Flash ESP32-C3 SuperMini - $(date)" >> "$LOG_FILE"
echo "========================================================" >> "$LOG_FILE"

log_msg "=== ⚡ Gravador de Firmware ESP32-C3 SuperMini ==="

# 1. Detecta porta serial
PORT="${1:-}"
if [ -z "$PORT" ]; then
    for candidate in /dev/ttyACM0 /dev/ttyACM1 /dev/ttyUSB0 /dev/ttyUSB1; do
        if [ -e "$candidate" ]; then
            PORT="$candidate"
            break
        fi
    done
fi

if [ -z "$PORT" ] || [ ! -e "$PORT" ]; then
    log_msg "❌ Nenhuma porta serial encontrada (/dev/ttyACM* ou /dev/ttyUSB*)."
    log_msg "👉 Conecte o ESP32-C3 SuperMini na porta USB do computador."
    exit 1
fi

log_msg "🔌 Porta Serial Detectada: $PORT"

# 2. Testa permissões de escrita na porta
if [ ! -w "$PORT" ]; then
    log_msg "⚠️ Sem permissão de escrita em $PORT. Tentando conceder acesso..."
    sudo chmod a+rw "$PORT" || true
fi

# 3. Localiza ferramentas
ARDUINO_CLI=$(which arduino-cli 2>/dev/null || echo "$HOME/.local/bin/arduino-cli")
if [ ! -x "$ARDUINO_CLI" ]; then
    log_msg "❌ 'arduino-cli' não encontrado no PATH."
    exit 1
fi

ESPTOOL=$(which esptool 2>/dev/null || which esptool.py 2>/dev/null || echo "$HOME/.local/bin/esptool")

# 4. Identificação do Hardware
log_msg "\n🔍 Identificando o chip na porta $PORT..."
if [ -x "$ESPTOOL" ]; then
    "$ESPTOOL" --port "$PORT" chip_id 2>&1 | tee -a "$LOG_FILE" || true
fi

# 5. Compilação do Firmware
log_msg "\n🔨 Compilando o firmware $SKETCH_DIR..."
"$ARDUINO_CLI" compile --fqbn "$FQBN" --build-property "$BUILD_FLAGS" "$SKETCH_DIR" 2>&1 | tee -a "$LOG_FILE"
log_msg "✅ Compilação concluída com sucesso!"

# 6. Gravação na Placa
log_msg "\n⚡ Gravando firmware no ESP32-C3 via $PORT..."
"$ARDUINO_CLI" upload -p "$PORT" --fqbn "$FQBN" "$SKETCH_DIR" 2>&1 | tee -a "$LOG_FILE"

log_msg "\n✅ Gravação finalizada com sucesso no ESP32-C3!"
log_msg "⏳ Aguardando 6 segundos para inicialização e conexão com o Wi-Fi..."
sleep 6

# 7. Teste de Recepção MQTT
log_msg "\n📡 Escutando telemetria do radar no Broker MQTT (192.168.1.7)..."
MQTT_HOST="192.168.1.7"
MQTT_USER="bruno"
MQTT_PASS="blurbang"

MQTT_PAYLOAD=$(timeout 7s mosquitto_sub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "home/outdoor/radar/#" -v -C 1 2>/dev/null || true)

if [ -n "$MQTT_PAYLOAD" ]; then
    log_msg "🎉 Comunicação MQTT confirmada com sucesso!"
    log_msg "📩 Mensagem recebida: $MQTT_PAYLOAD"
else
    log_msg "ℹ️ Telemetria imediata não capturada (o sensor pode estar aguardando detecção ou ciclo de status de 30s)."
fi

log_msg "\n💡 Dica: Para abrir o Monitor Serial e ver os pulsos do sensor LD2420 em tempo real:"
log_msg "   arduino-cli monitor -p $PORT -c baudrate=115200"
log_msg "========================================================"
