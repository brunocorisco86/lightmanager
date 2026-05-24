#!/bin/sh
# scripts/03_setup_mosquitto.sh
# Este script configura o Mosquitto no Alpine Linux (Raspberry Pi)

# Carrega o .env
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$DIR/../.env" ]; then
    source "$DIR/../.env"
fi

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

# 3. Criar arquivo de senhas para o usuário definido no .env
# Nota: mosquitto_passwd -b cria o arquivo se não existir (-c) ou adiciona
if [ -n "$MQTT_USER" ] && [ -n "$MQTT_PASSWORD" ]; then
    echo "==> Criando arquivo de senhas para o usuario $MQTT_USER..."
    mosquitto_passwd -b -c /etc/mosquitto/passwd "$MQTT_USER" "$MQTT_PASSWORD"
else
    echo "==> AVISO: MQTT_USER ou MQTT_PASSWORD nao definidos no .env. Ignorando criacao de passwd."
fi

echo "==> Ativando mosquitto no boot (OpenRC)..."
rc-update add mosquitto default

echo "==> Iniciando/Reiniciando serviço Mosquitto..."
rc-service mosquitto restart

echo "==> Verificando status..."
rc-service mosquitto status

echo "==> Mosquitto configurado com sucesso!"
