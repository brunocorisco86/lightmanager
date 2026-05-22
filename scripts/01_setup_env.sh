#!/bin/sh
echo "==> Configurando variaveis de ambiente (.env)..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Arquivo .env criado com sucesso! Por favor, edite-o com suas credenciais (Telegram, R2, etc)."
    echo "Dica: use 'nano .env'"
else
    echo "O arquivo .env ja existe. Nenhuma alteracao foi feita."
fi
