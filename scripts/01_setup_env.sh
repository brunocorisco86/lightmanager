#!/bin/sh
# scripts/01_setup_env.sh

# Definir raiz do projeto independentemente de onde o script é chamado
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
cd "$PROJECT_ROOT"

echo "==> Configurando variaveis de ambiente (.env)..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Arquivo .env criado com sucesso! Por favor, edite-o com suas credenciais."
    echo "Dica: use 'nano .env'"
else
    echo "O arquivo .env ja existe. Nenhuma alteracao foi feita."
fi
