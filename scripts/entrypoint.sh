#!/bin/bash
# scripts/entrypoint.sh
# Script centralizador para iniciar os serviços no boot

# Definir raiz do projeto independentemente de onde o script é chamado
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
cd "$PROJECT_ROOT"

PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python3"
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

case "$1" in
    api)
        echo "[$(date)] Iniciando Web API..." >> "$LOG_DIR/boot.log"
        exec "$PYTHON_BIN" web_api/main.py >> "$LOG_DIR/api.log" 2>&1
        ;;
    solar)
        echo "[$(date)] Iniciando Solar Worker..." >> "$LOG_DIR/boot.log"
        exec "$PYTHON_BIN" scripts/solar_worker.py >> "$LOG_DIR/solar.log" 2>&1
        ;;
    bot)
        echo "[$(date)] Iniciando Telegram Bot..." >> "$LOG_DIR/boot.log"
        exec "$PYTHON_BIN" bot/bot.py >> "$LOG_DIR/bot.log" 2>&1
        ;;
    *)
        echo "Uso: $0 {api|solar|bot}"
        exit 1
        ;;
esac
