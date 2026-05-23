#!/bin/sh
# scripts/03_setup_mosquitto.sh
# Este script configura o Mosquitto no Alpine Linux (Raspberry Pi)

echo "==> Configurando o Eclipse Mosquitto..."

# 1. Garante permissão na pasta de configs
mkdir -p /etc/mosquitto/conf.d

# 2. Criar arquivo de configuração com autenticação
cat << 'CONF' > /etc/mosquitto/mosquitto.conf
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
CONF

# 3. Criar arquivo de senhas para o usuário bruno/blurbang
# Nota: mosquitto_passwd -b cria o arquivo se não existir (-c) ou adiciona
mosquitto_passwd -b -c /etc/mosquitto/passwd bruno blurbang

echo "==> Ativando mosquitto no boot (OpenRC)..."
rc-update add mosquitto default

echo "==> Iniciando/Reiniciando serviço Mosquitto..."
rc-service mosquitto restart

echo "==> Verificando status..."
rc-service mosquitto status

echo "==> Mosquitto configurado com sucesso para o usuário 'bruno'!"
