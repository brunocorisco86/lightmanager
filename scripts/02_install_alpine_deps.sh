#!/bin/sh
# Este script deve ser rodado com sudo ou como root no Raspberry Pi
echo "==> Atualizando pacotes do Alpine..."
apk update

echo "==> Instalando dependencias (Mosquitto, Python, Postgres client, rclone, htop)..."
apk add mosquitto mosquitto-clients python3 py3-pip postgresql-client rclone htop

echo "==> Verificando dependencias Docker..."
if ! command -v docker >/dev/null 2>&1; then
    echo "Instalando Docker..."
    apk add docker docker-cli-compose
    rc-update add docker boot
    service docker start
fi

echo "==> Dependencias instaladas com sucesso!"
