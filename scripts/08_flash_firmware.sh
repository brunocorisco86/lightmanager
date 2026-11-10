#!/bin/bash
# scripts/08_flash_firmware.sh
# Gravador de Firmware Multi-Embarcado do Light Manager
# Suporta:
#   [1] Wemos D1 R1 (ESP8266)  - Fachada & Fundos (IP: 192.168.1.111)
#   [2] ESP32-C3 Supermini     - Muro & Auxiliar  (IP: 192.168.1.112)

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
cd "$PROJECT_ROOT"

LOG_DIR="logs"
mkdir -p "$LOG_DIR"

MQTT_HOST="192.168.1.7"
MQTT_USER="bruno"
MQTT_PASS="blurbang"

# ==========================================
# Seleção de Placa / Embarcado
# ==========================================
CHOICE="$1"

if [ -z "$CHOICE" ]; then
    echo "============================================================="
    echo "💡 Light Manager - Gravador de Firmware Multi-Embarcado"
    echo "============================================================="
    echo "  [1] Wemos D1 R1 (ESP8266)  - Fachada & Fundos (IP: 192.168.1.111)"
    echo "  [2] ESP32-C3 Supermini     - Muro & Auxiliar  (IP: 192.168.1.112)"
    echo "============================================================="
    read -rp "Selecione o embarcado para gravação [1 ou 2]: " CHOICE
fi

case "$CHOICE" in
    1|wemos|esp8266)
        BOARD_NAME="Wemos D1 R1 (ESP8266)"
        BOARD_CODE="wemos"
        FQBN="esp8266:esp8266:d1"
        SKETCH_DIR="firmware/wemos_light"
        BIN_PATH="firmware/wemos_light/wemos_light.ino.bin"
        TARGET_IP="192.168.1.111"
        PREFERRED_PORT="/dev/ttyUSB0"
        SET_TOPIC="home/outdoor/frente/set"
        STATE_TOPIC="home/outdoor/frente/state"
        LOG_FILE="$LOG_DIR/flash_wemos.log"
        EXPECTED_CHIP="ESP8266"
        ;;
    2|esp32|c3|supermini|muro)
        BOARD_NAME="ESP32-C3 Supermini"
        BOARD_CODE="esp32c3"
        FQBN="esp32:esp32:nologo_esp32c3_super_mini"
        SKETCH_DIR="firmware/esp32_c3_muro"
        BIN_PATH="firmware/esp32_c3_muro/esp32_c3_muro.ino.merged.bin"
        TARGET_IP="192.168.1.112"
        PREFERRED_PORT="/dev/ttyACM0"
        SET_TOPIC="home/outdoor/muro/set"
        STATE_TOPIC="home/outdoor/muro/state"
        LOG_FILE="$LOG_DIR/flash_esp32c3.log"
        EXPECTED_CHIP="ESP32-C3"
        ;;
    *)
        echo "❌ Opção inválida '$CHOICE'. Use '1' para Wemos D1 ou '2' para ESP32-C3."
        exit 1
        ;;
esac

log_msg() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

echo "========================================================" > "$LOG_FILE"
echo "📝 Log de Flash ($BOARD_NAME) - $(date)" >> "$LOG_FILE"
echo "========================================================" >> "$LOG_FILE"

log_msg "=== 🔌 Iniciando Gravação: $BOARD_NAME ==="
log_msg "📌 Destino: IP $TARGET_IP | Teste de Canal: $SET_TOPIC"

# ==========================================
# 1. Detecção da Porta Serial
# ==========================================
log_msg "\n=== 🔍 1. Identificando Porta Serial USB ==="
PORT="${PORT:-$PREFERRED_PORT}"

if [ ! -e "$PORT" ]; then
    # Tenta autodetectar alternativas
    if [ -e "/dev/ttyACM0" ]; then
        PORT="/dev/ttyACM0"
    elif [ -e "/dev/ttyUSB0" ]; then
        PORT="/dev/ttyUSB0"
    elif [ -e "/dev/ttyACM1" ]; then
        PORT="/dev/ttyACM1"
    elif [ -e "/dev/ttyUSB1" ]; then
        PORT="/dev/ttyUSB1"
    else
        log_msg "❌ Erro: Nenhuma porta serial detectada (/dev/ttyACM* ou /dev/ttyUSB*)!"
        log_msg "Certifique-se de que a placa $BOARD_NAME está conectada ao cabo USB."
        exit 1
    fi
fi

log_msg "✅ Porta Serial Detectada: $PORT"

# Permissão na porta
if [ ! -r "$PORT" ] || [ ! -w "$PORT" ]; then
    log_msg "⚠️ Ajustando permissões na porta serial $PORT..."
    sudo chmod a+rw "$PORT" 2>/dev/null || true
fi

# ==========================================
# 2. Localização de Ferramentas
# ==========================================
ESPTOOL=$(which esptool 2>/dev/null || which esptool.py 2>/dev/null || echo "$HOME/.local/bin/esptool")
if [ ! -x "$(command -v "$ESPTOOL")" ]; then
    log_msg "❌ Erro: 'esptool' não encontrado! Instale com: pip install esptool"
    exit 1
fi

ARDUINO_CLI=$(which arduino-cli 2>/dev/null || echo "$HOME/.local/bin/arduino-cli")

# ==========================================
# 3. Identificação do Hardware Conectado
# ==========================================
log_msg "\n=== 🔍 2. Consultando Chip Conectado via esptool ==="
CHIP_DETECT=$("$ESPTOOL" --port "$PORT" chip-id 2>&1 || true)
echo "$CHIP_DETECT" >> "$LOG_FILE"

if echo "$CHIP_DETECT" | grep -qi "ESP32-C3"; then
    DETECTED_CHIP="ESP32-C3"
elif echo "$CHIP_DETECT" | grep -qi "ESP8266"; then
    DETECTED_CHIP="ESP8266"
else
    DETECTED_CHIP="Desconhecido"
fi

log_msg "Chip Físico Detectado na porta $PORT: $DETECTED_CHIP"

if [ "$DETECTED_CHIP" != "$EXPECTED_CHIP" ]; then
    log_msg "⚠️ AVISO: Você selecionou '$BOARD_NAME' (esperado: $EXPECTED_CHIP), mas o chip detectado na porta $PORT foi '$DETECTED_CHIP'."
    read -rp "Deseja continuar mesmo assim? (s/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[sSyY]$ ]]; then
        log_msg "Operação abortada pelo usuário."
        exit 1
    fi
fi

# ==========================================
# 4. Compilação do Firmware
# ==========================================
log_msg "\n=== 🔨 3. Compilando Sketch com arduino-cli ==="
log_msg "Compilando $SKETCH_DIR para $FQBN..."
"$ARDUINO_CLI" compile --fqbn "$FQBN" "$SKETCH_DIR" --output-dir "$SKETCH_DIR" 2>&1 | tee -a "$LOG_FILE"
log_msg "✅ Compilação finalizada com sucesso."

# ==========================================
# 5. Gravação (Flash)
# ==========================================
log_msg "\n=== ⚡ 4. Gravando Firmware na Placa ==="

if [ "$BOARD_CODE" = "esp32c3" ]; then
    log_msg "💡 Dica ESP32-C3 Supermini:"
    log_msg "   - O chip possui CDC/JTAG nativo e deve reiniciar automaticamente em modo download."
    log_msg "   - Caso o esptool trave em 'Connecting...', segure o botão BOOT (GPIO9), aperte e solte RST, e então solte BOOT."
    log_msg ""
    
    # Gravando via arduino-cli upload ou esptool com imagem unificada
    if [ -f "$SKETCH_DIR/esp32_c3_muro.ino.merged.bin" ]; then
        log_msg "⚡ Gravando imagem completa (merged.bin) em 0x0 via esptool..."
        "$ESPTOOL" --chip esp32c3 --port "$PORT" --baud 460800 write-flash 0x0 "$SKETCH_DIR/esp32_c3_muro.ino.merged.bin" 2>&1 | tee -a "$LOG_FILE"
    else
        log_msg "⚡ Executando upload via arduino-cli..."
        "$ARDUINO_CLI" upload -p "$PORT" --fqbn "$FQBN" "$SKETCH_DIR" 2>&1 | tee -a "$LOG_FILE"
    fi
else
    # Wemos D1 R1 (ESP8266)
    log_msg "⚡ Gravando $BIN_PATH em 0x0 via esptool (460800 baud)..."
    "$ESPTOOL" --port "$PORT" --baud 460800 write-flash 0x0 "$BIN_PATH" 2>&1 | tee -a "$LOG_FILE"
fi

log_msg "\n✅ Gravação concluída com sucesso!"

# ==========================================
# 6. Testes de Integridade Pós-Flash
# ==========================================
log_msg "\n=== 🔍 5. Validação de Rede & Comunicação MQTT ==="
log_msg "⏳ Aguardando 8 segundos para a placa inicializar e autenticar no Wi-Fi..."
sleep 8

log_msg "🔍 Testando conectividade de rede com o IP $TARGET_IP..."
if ping -c 3 -W 2 "$TARGET_IP" 2>&1 | tee -a "$LOG_FILE"; then
    log_msg "✅ Conexão IP OK: $TARGET_IP está respondendo a pings."
else
    log_msg "⚠️ Alerta: A placa não respondeu ao ping em $TARGET_IP ainda."
    log_msg "Aguardando mais 5 segundos..."
    sleep 5
    if ! ping -c 2 -W 2 "$TARGET_IP" > /dev/null 2>&1; then
        log_msg "❌ Falha no Ping: Placa não respondeu em $TARGET_IP. Verifique credenciais Wi-Fi ou roteador."
        exit 1
    fi
fi

# Teste MQTT com envio de ON e OFF e verificação de ACK no state topic
log_msg "\n🔍 Testando canal MQTT em $SET_TOPIC..."
MQTT_OUT=$(mktemp)
timeout 7s mosquitto_sub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$STATE_TOPIC" -v > "$MQTT_OUT" &
SUB_PID=$!
sleep 1.5

log_msg "💡 [PC -> Broker] Enviando 'ON' para $SET_TOPIC..."
mosquitto_pub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$SET_TOPIC" -m "ON" 2>&1 | tee -a "$LOG_FILE"
sleep 1.5

log_msg "🔌 [PC -> Broker] Enviando 'OFF' para $SET_TOPIC..."
mosquitto_pub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$SET_TOPIC" -m "OFF" 2>&1 | tee -a "$LOG_FILE"
sleep 1.5

wait $SUB_PID 2>/dev/null || true

log_msg "=== 📨 Respostas (ACK) recebidas da placa via Broker ==="
cat "$MQTT_OUT" | tee -a "$LOG_FILE"
log_msg "========================================================"

ACK_ON=$(grep -c "ON" "$MQTT_OUT" || true)
ACK_OFF=$(grep -c "OFF" "$MQTT_OUT" || true)
rm -f "$MQTT_OUT"

if [ "$ACK_ON" -gt 0 ] && [ "$ACK_OFF" -gt 0 ]; then
    log_msg "✅ VALIDAÇÃO MQTT OK! A placa $BOARD_NAME processou os comandos e devolveu ACKs."
    log_msg "\n🎉 Deploy e Testes de Firmware concluídos com 100% de sucesso!"
else
    log_msg "❌ ERRO: A placa não enviou os ACKs esperados de ON/OFF pelo broker no tópico $STATE_TOPIC."
    exit 1
fi
