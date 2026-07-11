# 📦 Configuração de Backup: Cloudflare R2

Este documento descreve o processo de comissionamento para os backups do banco de dados do Light Manager no Cloudflare R2, mantendo-se dentro do **Free Tier** e com máxima eficiência de recursos.

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

```env
R2_ACCOUNT_ID=seu_account_id
R2_ACCESS_KEY_ID=sua_access_key
R2_SECRET_ACCESS_KEY=sua_secret_key
R2_BUCKET_NAME=lightmanager-backups
R2_ENDPOINT_URL=sua_url_s3_r2
```

### 2.2 Dependências
O script utiliza o `rclone` e o `docker`. Certifique-se de que estão instalados:
```bash
sudo apk add rclone  # Alpine Linux
# Ou instale via script de comissionamento do projeto:
./scripts/02_install_alpine_deps.sh
```

## 3. Execução e Teste

O script `scripts/backup_r2.sh` é resiliente e higieniza automaticamente a `R2_ENDPOINT_URL` caso ela contenha o nome do bucket no final, garantindo compatibilidade com o rclone.

**Para testar manualmente:**
```bash
bash scripts/backup_r2.sh
```
Se tudo der certo, você verá uma mensagem de sucesso em verde e o arquivo `.tar.gz` compactado aparecerá no painel da Cloudflare.

## 4. Agendamento (Crontab)

Para realizar o backup mensalmente (todo dia 1 às 03:00) e registrar os logs, adicione ao seu crontab (`crontab -e`):

```cron
00 03 1 * * /bin/bash /home/bruno/lightmanager/scripts/backup_r2.sh >> /home/bruno/lightmanager/logs/backup.log 2>&1
```

## 5. Política de Retenção e Custos (Free Tier)

*   **Operações:** O script usa `rclone copy`, que minimiza operações de listagem e custos de API.
*   **Banda e CPU:** A frequência do backup é configurada de forma a manter o consumo de processamento e rede sob controle no Raspberry Pi 3B.
*   **Retenção de Arquivos:** O script gerencia de forma autônoma a retenção, mantendo apenas os **5 backups mais recentes** no Cloudflare R2 para garantir a segurança dos dados sob a cota gratuita.
