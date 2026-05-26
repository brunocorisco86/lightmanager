#!/bin/bash
# scripts/backup_r2.sh

# Cores para logs
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
BACKUP_TEMP="$PROJECT_ROOT/backups_tmp"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M)

# 1. Carregar variáveis
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
else
    echo -e "${RED}Erro: Arquivo .env não encontrado.${NC}"
    exit 1
fi

echo -e "${GREEN}==> Iniciando Backup para Cloudflare R2...${NC}"

# 2. Configurar Rclone via Variáveis de Ambiente (Sem necessidade de arquivo de config)
export RCLONE_CONFIG_R2_TYPE=s3
export RCLONE_CONFIG_R2_PROVIDER=Cloudflare
export RCLONE_CONFIG_R2_ACCESS_KEY_ID=$R2_ACCESS_KEY_ID
export RCLONE_CONFIG_R2_SECRET_ACCESS_KEY=$R2_SECRET_ACCESS_KEY
# Usa a URL configurada no .env (Endpoint S3 compatível do Cloudflare R2)
export RCLONE_CONFIG_R2_ENDPOINT=$R2_ENDPOINT_URL
export RCLONE_CONFIG_R2_ACL=private

# 3. Preparar diretório temporário
mkdir -p "$BACKUP_TEMP"

# 4. Dump do Banco de Dados (Postgres no Docker)
echo "--> Realizando dump do banco de dados..."
SQL_FILE="db_backup_$TIMESTAMP.sql"
# Usa o container Docker já que ele possui as ferramentas do postgres instaladas
docker exec postgres_db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_TEMP/$SQL_FILE"

# 5. Compactar apenas o dump (Economiza espaço no R2)
echo "--> Compactando dump..."
tar -czf "$BACKUP_TEMP/$SQL_FILE.tar.gz" -C "$BACKUP_TEMP" "$SQL_FILE"

# 6. Sincronizar com R2
echo "--> Fazendo upload para o bucket: $R2_BUCKET_NAME"
rclone copy "$BACKUP_TEMP/$SQL_FILE.tar.gz" "R2:$R2_BUCKET_NAME/backups/" --progress

# 7. Manter apenas os 5 últimos backups no R2 (Política de Retenção Mensal)
echo "--> Verificando retenção (mantendo apenas os 5 mais recentes)..."
# Lista arquivos ordenados por nome, pega todos exceto os 5 mais recentes (os últimos da lista)
OLD_BACKUPS=$(rclone lsf "R2:$R2_BUCKET_NAME/backups/" --sort name | head -n -5)

if [ -n "$OLD_BACKUPS" ]; then
    for file in $OLD_BACKUPS; do
        echo "Excluindo backup antigo: $file"
        rclone delete "R2:$R2_BUCKET_NAME/backups/$file"
    done
fi

# 8. Limpeza local
echo "--> Limpando arquivos temporários locais..."
rm -rf "$BACKUP_TEMP"

echo -e "${GREEN}✅ Backup concluído com sucesso no Cloudflare R2!${NC}"
