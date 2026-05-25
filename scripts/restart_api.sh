#!/bin/bash
# scripts/restart_api.sh

# Cores para logs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
API_LOG="$PROJECT_ROOT/logs/api.log"

echo -e "${BLUE}==> Reiniciando Web API do Light Manager...${NC}"

# 1. Parar processos antigos
echo "--> Parando processos Python/Uvicorn existentes..."
pkill -f "web_api/main.py" || true
sleep 1

# 2. Iniciar API em background
echo "--> Iniciando Web API..."
cd "$PROJECT_ROOT"
source .venv/bin/activate
nohup python3 web_api/main.py > "$API_LOG" 2>&1 &

# 3. Verificar se subiu
sleep 2
PID=$(pgrep -f "web_api/main.py")

if [ -n "$PID" ]; then
    echo -e "${GREEN}✅ API reiniciada com sucesso! (PID: $PID)${NC}"
    echo "Logs sendo gravados em: $API_LOG"
else
    echo -e "${RED}❌ Falha ao iniciar a API. Verifique os logs em $API_LOG${NC}"
    exit 1
fi
