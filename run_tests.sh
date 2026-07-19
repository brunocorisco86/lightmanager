#!/bin/bash
# run_tests.sh
# Script utilitário para executar toda a suíte de testes do Light Manager

# Cores para o terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==> Iniciando Suíte de Testes do Light Manager...${NC}"

# Verifica se o ambiente virtual existe
if [ ! -d ".venv" ]; then
    echo -e "${RED}Erro: Ambiente virtual (.venv) não encontrado. Execute scripts/setup.sh primeiro.${NC}"
    exit 1
fi

# Ativa o ambiente e configura o PYTHONPATH
source .venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.

# 1. Testes Unitários e de Integração (Pytest)
echo -e "\n${GREEN}1. Executando Pytest (API, Web, Auth, Config, Reliability, Telegram, Backup, Bot)...${NC}"
./.venv/bin/python3 -m pytest tests/test_api.py tests/test_web_api.py tests/test_timezone.py tests/test_auth.py tests/test_web_config.py tests/test_command_reliability.py tests/test_telegram.py tests/test_backup.py tests/test_bot_integrity.py tests/test_weather_sync.py tests/test_automation_improvements.py tests/test_housekeeping.py -v | tee logs/tests.log

# Captura o status do pytest (temos que pegar o status do pytest, não do tee. PIPESTATUS[0] funciona no bash)
PYTEST_RES=${PIPESTATUS[0]}

# 2. Testes de Benchmark e Integridade do Worker
echo -e "\n${GREEN}2. Executando Benchmark do Solar Worker...${NC}"
./.venv/bin/python3 tests/benchmark_solar_worker.py 2>&1 | tee -a logs/tests.log

BENCH_RES=$?

echo -e "\n${BLUE}==========================================${NC}"
if [ $PYTEST_RES -eq 0 ] && [ $BENCH_RES -eq 0 ]; then
    echo -e "${GREEN}✅ TODOS OS TESTES PASSARAM COM SUCESSO!${NC}"
else
    echo -e "${RED}❌ ALGUNS TESTES FALHARAM.${NC}"
    exit 1
fi
