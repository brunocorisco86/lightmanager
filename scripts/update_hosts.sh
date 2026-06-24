#!/bin/bash
# scripts/update_hosts.sh
# Atualiza dinamicamente o mapeamento de IP para api.open-meteo.com no /etc/hosts

DOMAIN="api.open-meteo.com"
HOSTS_FILE="/etc/hosts"

echo "=== Iniciando atualização de DNS estático para $DOMAIN ==="

# 1. Resolve o IP atual do domínio
NEW_IP=""
if command -v dig > /dev/null 2>&1; then
    NEW_IP=$(dig +short "$DOMAIN" | tail -n1)
elif command -v nslookup > /dev/null 2>&1; then
    NEW_IP=$(nslookup "$DOMAIN" | awk '/^Address: / { print $2 }' | tail -n1)
elif command -v host > /dev/null 2>&1; then
    NEW_IP=$(host "$DOMAIN" | awk '/has address/ { print $4 }' | tail -n1)
fi

# Verifica se o IP é válido (formato básico IPv4)
if [[ ! "$NEW_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Erro: Não foi possível obter um IP válido para $DOMAIN (obtido: '$NEW_IP'). Mantendo configuração anterior."
    exit 1
fi

echo "IP atual de $DOMAIN resolvido: $NEW_IP"

# 2. Verifica se a entrada já existe no /etc/hosts
if grep -q "$DOMAIN" "$HOSTS_FILE"; then
    # Entrada existe. Vamos ver se o IP mudou
    OLD_IP=$(grep "$DOMAIN" "$HOSTS_FILE" | awk '{print $1}')
    if [ "$OLD_IP" = "$NEW_IP" ]; then
        echo "O IP não mudou ($OLD_IP). Nenhuma ação necessária."
        exit 0
    else
        echo "IP mudou de $OLD_IP para $NEW_IP. Atualizando $HOSTS_FILE..."
        # Substitui a linha antiga pela nova
        sudo sed -i "s/.*$DOMAIN/$NEW_IP $DOMAIN/g" "$HOSTS_FILE"
        echo "Mapeamento atualizado com sucesso!"
    fi
else
    # Entrada não existe. Vamos adicionar
    echo "Entrada não encontrada no $HOSTS_FILE. Adicionando..."
    echo "$NEW_IP $DOMAIN" | sudo tee -a "$HOSTS_FILE" > /dev/null
    echo "Mapeamento adicionado com sucesso!"
fi
