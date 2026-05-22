#!/bin/bash
# scripts/05_docker_management.sh

# Cores para o terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."

cd "$PROJECT_ROOT"

case "$1" in
    up)
        echo -e "${GREEN}==> Subindo a infraestrutura (Postgres)...${NC}"
        docker-compose up -d
        ;;
    down)
        echo -e "${YELLOW}==> Parando os containers...${NC}"
        docker-compose down
        ;;
    restart)
        echo -e "${YELLOW}==> Reiniciando containers...${NC}"
        docker-compose restart
        ;;
    rebuild)
        echo -e "${GREEN}==> Forçando Rebuild/Pull de imagens e reiniciando...${NC}"
        docker-compose down
        docker-compose pull
        docker-compose up -d --force-recreate
        ;;
    status)
        docker-compose ps
        ;;
    logs)
        docker-compose logs -f
        ;;
    *)
        echo "Uso: $0 {up|down|restart|rebuild|status|logs}"
        exit 1
esac
