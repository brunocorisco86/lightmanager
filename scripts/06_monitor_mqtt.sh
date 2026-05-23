#!/bin/bash
# scripts/06_monitor_mqtt.sh

# Definir raiz do projeto independentemente de onde o script é chamado
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
cd "$PROJECT_ROOT"

echo "=== Verificando Saúde do Mosquitto ==="

# 1. Verifica se o processo está rodando
if pgrep -x "mosquitto" > /dev/null; then
    echo "✅ Mosquitto está rodando (PID: $(pgrep -x mosquitto))"
else
    echo "❌ Mosquitto NÃO está rodando!"
    exit 1
fi

# 2. Verifica se a porta 1883 está aberta
if nc -z localhost 1883 > /dev/null; then
    echo "✅ Porta 1883 está escutando."
else
    echo "❌ Porta 1883 NÃO está aberta (verifique o firewall ou configuração)!"
    exit 1
fi

# 3. Monitoramento
echo ""
echo "=== Monitorando comunicação em tempo real (Ctrl+C para parar) ==="
echo "================================================================"

# Verifica se o cliente MQTT está instalado
if ! command -v mosquitto_sub &> /dev/null; then
    echo "Erro: 'mosquitto_sub' não encontrado."
    echo "Instale-o no Alpine com: apk add mosquitto-clients"
    exit 1
fi

# -t '#' assina todos os tópicos
# -v imprime o tópico junto com a mensagem (verbose)
mosquitto_sub -h localhost -t '#' -v
