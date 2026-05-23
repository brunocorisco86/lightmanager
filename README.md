# Light Manager

Este repositório contém a solução completa para o controle inteligente de iluminação externa residencial, projetado para operar com foco no minimalismo de recursos (RAM/CPU) em um Raspberry Pi 3B com Alpine Linux.

## Funcionalidades
- 💡 **Controle Remoto:** Acione suas luzes pela Interface Web ou via Bot do Telegram.
- 🌅 **Automação Solar Inteligente:** Liga e desliga as luzes automaticamente baseado no horário do pôr do sol/aurora da sua latitude, com suporte a "offsets" personalizados de minutos (ex: Ligar 15 minutos *antes* do pôr do sol).
- 📊 **Monitoramento e Histórico:** Gráficos no site e relatórios no Telegram demonstrando o consumo e tempo de uso das lâmpadas.
- ☁️ **Backups Resilientes:** Sistema auto-gerenciado de dump do Postgres para o Cloudflare R2 usando `rclone`.

## Organização do Repositório
Consulte a pasta `docs/` para aprofundar seu conhecimento na estrutura do projeto:
- `docs/STACK.md`: Tecnologias utilizadas.
- `docs/ROADMAP.md`: Próximos passos para o comissionamento.
- `docs/BACKUP_MANUAL.md`: Instruções sobre os backups na nuvem.

## Como começar
1. Copie o arquivo `.env.example` para `.env` e ajuste suas senhas/tokens e latitude/longitude.
2. Siga os scripts enumerados na pasta `scripts/` (em ordem numérica: 00, 01, 02, etc.) para provisionar o ambiente Python, pacotes do Linux e dependências.
3. Use o `crontab_template.txt` para configurar os gatilhos no seu SO.
