#!/bin/bash
# scripts/08_flash_wemos.sh
# Wrapper de compatibilidade para o novo gravador unificado scripts/08_flash_firmware.sh
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/08_flash_firmware.sh" "${1:-1}"
