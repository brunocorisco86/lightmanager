#!/bin/bash
# scripts/setup.sh

# Cores para o terminal
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}==> Iniciando configuração do ambiente Python...${NC}"

# Verifica se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Erro: Python3 não encontrado. Instale-o com 'apk add python3'."
    exit 1
fi

# Cria o ambiente virtual se não existir
if [ ! -d ".venv" ]; then
    echo -e "${GREEN}==> Criando ambiente virtual (.venv)...${NC}"
    python3 -m venv .venv
fi

# Ativa o ambiente e instala dependências
echo -e "${GREEN}==> Instalando/Atualizando dependências...${NC}"
source .venv/bin/activate
pip install --upgrade pip
pip install -r bot/requirements.txt

echo -e "${GREEN}✅ Ambiente configurado com sucesso!${NC}"
echo -e "Para ativar, use: ${GREEN}source .venv/bin/activate${NC}"
