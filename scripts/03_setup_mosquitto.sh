#!/bin/sh
# Este script deve ser rodado com sudo ou como root no Raspberry Pi
echo "==> Configurando o Eclipse Mosquitto..."

# Criar arquivo de configuracao basico (permite acesso local/anonimo para inicio)
cat << 'CONF' > /etc/mosquitto/mosquitto.conf
listener 1883
allow_anonymous true
# futuramente:
# password_file /etc/mosquitto/passwd
# allow_anonymous false
CONF

echo "==> Ativando mosquitto no boot (OpenRC)..."
rc-update add mosquitto default

echo "==> Iniciando servico Mosquitto..."
rc-service mosquitto restart

echo "==> Mosquitto rodando na porta 1883!"
