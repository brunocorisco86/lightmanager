#!/bin/bash
# scripts/restart_solar.sh
# Script para reiniciar o serviço Solar Worker & Event Logger

PROJECT_ROOT="/home/bruno/lightmanager"

echo "==> Localizando e parando o Solar Worker..."
# pkill -f procura pelo nome do script nos processos
pkill -f solar_worker.py

# Pequena pausa para garantir que o processo liberou a porta/recursos
sleep 2

echo "==> Iniciando o Solar Worker via entrypoint..."
# Inicia em background (usando nohup para não morrer ao fechar o terminal)
nohup /bin/bash "$PROJECT_ROOT/scripts/entrypoint.sh" solar > /dev/null 2>&1 &

echo "==> Solar Worker reiniciado com sucesso!"
echo "==> Você pode acompanhar o log em tempo real com:"
echo "    tail -f $PROJECT_ROOT/logs/solar.log"
