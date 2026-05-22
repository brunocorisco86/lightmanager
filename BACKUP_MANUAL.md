# Manual de Backup - Cloudflare R2

Este documento descreve como configurar e validar o sistema de backup automático para o seu Light Manager.

## 1. Pré-requisitos
1.  **Conta Cloudflare:** Ter um Bucket R2 criado (ex: `light-manager-backups`).
2.  **Tokens de API:** Criar um "R2 API Token" com permissão de Edit (Read/Write) e copiar o `Access Key ID` e `Secret Access Key`.
3.  **Rclone Instalado:** No Alpine, rodar `./scripts/02_install_alpine_deps.sh`.

## 2. Configuração
Edite o arquivo `.env` na raiz do projeto e preencha:
```env
R2_ACCOUNT_ID=seu_id_de_conta_cloudflare
R2_ACCESS_KEY_ID=sua_chave_acesso
R2_SECRET_ACCESS_KEY=sua_chave_secreta
R2_BUCKET_NAME=nome_do_seu_bucket
```

## 3. Teste Manual
Antes de automatizar, rode o script manualmente para garantir que as permissões estão corretas:
```bash
./scripts/backup_r2.sh
```
Se tudo der certo, você verá uma mensagem verde e o arquivo `.tar.gz` aparecerá no painel da Cloudflare.

## 4. Comissionamento (Automação)
Para configurar o agendamento semanal no Raspberry Pi:

1.  Dê permissão de execução: `chmod +x scripts/backup_r2.sh`
2.  Abra o crontab do seu usuário: `crontab -e`
3.  Copie o conteúdo do arquivo `crontab_template.txt` e cole no final.
4.  Salve e saia.

## 5. Estratégia de Custos (Free Tier)
- **Operações:** O script usa `rclone copy`, que minimiza operações de listagem.
- **Frequência:** Semanal é ideal para manter o uso de banda e CPU baixo no Pi 3B.
- **Retenção:** Recomenda-se configurar uma "Lifecycle Policy" no painel da Cloudflare para deletar arquivos com mais de 90 dias, mantendo o armazenamento sempre abaixo de 10GB.
