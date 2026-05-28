#!/bin/bash
# scripts/restart_bot.sh
# Mata instâncias antigas do bot e inicia uma nova em background

# Definir raiz do projeto independentemente de onde o script é chamado
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
cd "$PROJECT_ROOT"

LOG_FILE="$PROJECT_ROOT/logs/bot.log"

echo "[$(date)] 🔄 Reiniciando Telegram Bot..." >> "$LOG_FILE"

# 1. Mata qualquer processo existente do bot
PID=$(pgrep -f "bot/bot.py")
if [ -n "$PID" ]; then
    echo "[$(date)] Matando processo antigo (PID: $PID)..." >> "$LOG_FILE"
    kill -9 $PID
fi

# 2. Inicia o bot via entrypoint (que já redireciona logs)
# Usa nohup para garantir que continue rodando após o shell fechar
cd "$PROJECT_ROOT"
nohup /bin/bash scripts/entrypoint.sh bot > /dev/null 2>&1 &

echo "[$(date)] ✅ Bot reiniciado com sucesso." >> "$LOG_FILE"
