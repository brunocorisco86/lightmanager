#!/bin/bash
# Script de gravação rápida e monitor serial do teste minimalista
set -e

SKETCH_DIR="firmware/test_ld2420_minimal"
PORT="/dev/ttyACM0"
FQBN="esp32:esp32:esp32c3"

echo "=== ⚡ Compilando Sketch Minimalista do Sensor ==="
arduino-cli compile --fqbn "$FQBN" \
  --build-property "build.extra_flags=-DARDUINO_USB_MODE=1 -DARDUINO_USB_CDC_ON_BOOT=1" \
  "$SKETCH_DIR"

echo "=== ⚡ Gravando na porta $PORT ==="
arduino-cli upload -p "$PORT" --fqbn "$FQBN" "$SKETCH_DIR"

echo "=== ✅ Gravado com sucesso! Abrindo Monitor Serial (Ctrl+C para sair) ==="
arduino-cli monitor -p "$PORT" -c baudrate=115200
