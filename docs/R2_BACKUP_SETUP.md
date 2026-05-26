# 📦 Configuração de Backup: Cloudflare R2

Este documento descreve o processo de comissionamento para os backups mensais do banco de dados do Light Manager no Cloudflare R2, mantendo-se dentro do **Free Tier**.

## 1. Configuração no Painel Cloudflare

1.  **Criar Bucket:**
    *   Vá para **R2** > **Create Bucket**.
    *   Nome Sugerido: `lightmanager-backups`.
2.  **Obter Account ID:**
    *   O Account ID está visível na página principal do R2.
3.  **Gerar API Token:**
    *   Clique em **Manage R2 API Tokens** > **Create API Token**.
    *   Permissões: **Object Read & Write**.
    *   Escopo: Selecione apenas o bucket criado.
    *   Salve o **Access Key ID** e o **Secret Access Key**.

## 2. Configuração no Servidor (Local)

### 2.1 Atualizar o `.env`
Preencha as seguintes variáveis no seu arquivo `.env` na raiz do projeto:

```bash
R2_ACCESS_KEY_ID=sua_access_key
R2_SECRET_ACCESS_KEY=sua_secret_key
R2_BUCKET_NAME=lightmanager-backups
R2_ENDPOINT_URL=sua_url_s3_r2
```

### 2.2 Dependências
O script utiliza o `rclone` e o `docker`. Certifique-se de que estão instalados:
```bash
sudo apk add rclone  # Alpine Linux
```

## 3. Execução e Teste

O script `scripts/backup_r2.sh` é resiliente e higieniza automaticamente a `R2_ENDPOINT_URL` caso ela contenha o nome do bucket no final, garantindo compatibilidade com o rclone.

**Para testar manualmente:**
```bash
bash scripts/backup_r2.sh
```

## 4. Agendamento (Crontab)

Para realizar o backup mensalmente (todo dia 1 às 03:00) e registrar os logs, adicione ao seu crontab (`crontab -e`):

```cron
00 03 1 * * /bin/bash /home/bruno/lightmanager/scripts/backup_r2.sh >> /home/bruno/lightmanager/logs/backup.log 2>&1
```

## 5. Política de Retenção
O script está configurado para manter apenas os **5 últimos backups** no Cloudflare R2. Isso garante o uso mínimo de espaço e segurança dos dados.
