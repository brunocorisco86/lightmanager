#!/bin/bash
# scripts/restart_solar.sh

# Cores para logs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
LOG_FILE="$PROJECT_ROOT/logs/solar.log"

echo -e "${BLUE}==> Reiniciando Solar Worker do Light Manager...${NC}"

# 1. Parar processos antigos
echo "--> Parando processos solar_worker.py existentes..."
pkill -f "scripts/solar_worker.py" || true
sleep 1

# 2. Iniciar em background
echo "--> Iniciando Solar Worker..."
cd "$PROJECT_ROOT"
source .venv/bin/activate
nohup python3 scripts/solar_worker.py > "$LOG_FILE" 2>&1 &

# 3. Verificar se subiu
sleep 2
PID=$(pgrep -f "scripts/solar_worker.py")

if [ -n "$PID" ]; then
    echo -e "${GREEN}✅ Solar Worker reiniciado com sucesso! (PID: $PID)${NC}"
    echo "Logs sendo gravados em: $LOG_FILE"
else
    echo -e "${RED}❌ Falha ao iniciar o Solar Worker. Verifique os logs em $LOG_FILE${NC}"
    exit 1
fi
