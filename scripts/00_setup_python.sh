#!/bin/bash
# scripts/setup.sh

# Definir raiz do projeto independentemente de onde o script é chamado
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
cd "$PROJECT_ROOT"

# Cores para o terminal
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}==> Iniciando configuração do ambiente Python na raiz...${NC}"

# Verifica se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Erro: Python3 não encontrado. Instale-o com 'apk add python3'."
    exit 1
fi

# Cria o ambiente virtual na RAIZ do projeto
if [ ! -d ".venv" ]; then
    echo -e "${GREEN}==> Criando ambiente virtual (.venv) em $PROJECT_ROOT...${NC}"
    python3 -m venv .venv
fi

# Ativa o ambiente e instala dependências
echo -e "${GREEN}==> Instalando/Atualizando dependências...${NC}"
source .venv/bin/activate
pip install --upgrade pip
pip install -r bot/requirements.txt
# Dependências adicionais para o sincronizador de offsets meteorológicos
pip install openmeteo-requests
pip install requests-cache retry-requests numpy pandas

echo -e "${GREEN}✅ Ambiente configurado com sucesso!${NC}"
echo -e "Para ativar, use: ${GREEN}source .venv/bin/activate${NC}"
