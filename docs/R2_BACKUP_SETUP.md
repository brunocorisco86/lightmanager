# 📦 Configuração de Backup: Cloudflare R2

Este documento descreve o processo de comissionamento para os backups semanais do banco de dados do Light Manager no Cloudflare R2, mantendo-se dentro do **Free Tier**.

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
R2_ACCOUNT_ID=seu_account_id
R2_ACCESS_KEY_ID=sua_access_key
R2_SECRET_ACCESS_KEY=sua_secret_key
R2_BUCKET_NAME=lightmanager-backups
```

### 2.2 Dependências
O script utiliza o `rclone`. Certifique-se de que ele está instalado:
```bash
sudo apk add rclone  # Alpine Linux
# ou
sudo apt install rclone # Debian/Ubuntu
```

## 3. Execução e Teste

O script `scripts/backup_r2.sh` é resiliente e não requer configuração prévia do rclone (ele usa variáveis de ambiente para se configurar em tempo de execução).

**Para testar manualmente:**
```bash
bash scripts/backup_r2.sh
```

## 4. Agendamento (Crontab)

Para realizar o backup semanalmente (todo domingo às 03:00) e registrar os logs, adicione ao seu crontab (`crontab -e`):

```cron
00 03 * * 0 /bin/bash /home/bruno/lightmanager/scripts/backup_r2.sh >> /home/bruno/lightmanager/logs/backup.log 2>&1
```

## 5. Política de Retenção
O script está configurado para manter apenas os **3 últimos backups** no Cloudflare R2. Isso garante o uso mínimo de espaço e mantém você seguro dentro do limite gratuito de 10GB.
