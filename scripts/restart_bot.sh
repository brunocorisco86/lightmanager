#!/bin/bash
# scripts/restart_bot.sh
# Mata instâncias antigas do bot e inicia uma nova em background

# Cores para logs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Definir raiz do projeto independentemente de onde o script é chamado
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
LOG_FILE="$PROJECT_ROOT/logs/bot.log"

echo "[$(date)] 🔄 Reiniciando Telegram Bot..." >> "$LOG_FILE"

# 1. Mata qualquer processo existente do bot
PID=$(pgrep -f "bot/bot.py")
if [ -n "$PID" ]; then
    echo "[$(date)] Matando processo antigo (PID: $PID)..." >> "$LOG_FILE"
    kill -9 $PID
    sleep 1
fi

# 2. Inicia o bot com venv ativado para garantir as dependências e caminhos correctos
cd "$PROJECT_ROOT"
source .venv/bin/activate
nohup python3 bot/bot.py >> "$LOG_FILE" 2>&1 &

# 3. Verificar se subiu
sleep 2
PID=$(pgrep -f "bot/bot.py")

if [ -n "$PID" ]; then
    echo "[$(date)] ✅ Bot reiniciado com sucesso. (PID: $PID)" >> "$LOG_FILE"
else
    echo "[$(date)] ❌ Falha ao iniciar o Bot do Telegram." >> "$LOG_FILE"
    exit 1
fi

