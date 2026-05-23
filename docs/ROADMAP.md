# Light Manager - Roadmap & Next Steps

## 1. Concluído ✅
- Estrutura base de diretórios e arquitetura.
- Configuração inicial do PostgreSQL via Docker.
- Instalação e comissionamento do Mosquitto nativo (Alpine).
- Modelagem do Banco de Dados (Suporte a múltiplos pontos de luz e offsets solares).
- Scripts de relatórios diários (CSV/JSON export via psql).
- Interface Web (Vanilla JS + FastAPI).
- Bot Telegram interativo (Aiogram, leitura de RAM, CPU e relatórios).
- Automação Solar inteligente (Solar Worker com retry e cache).
- Rotina de Backup otimizada e resiliente para o Cloudflare R2 (Rclone).
- Refatoração do Git e higienização do repositório.

## 2. Next Steps (Para Comissionamento) 🚧
- [ ] Gravar a imagem do Alpine Linux no Raspberry Pi 3B.
- [ ] Clonar este repositório no Pi.
- [ ] Rodar `./scripts/00_setup_python.sh` para preparar o ambiente.
- [ ] Rodar `./scripts/01_setup_env.sh` para criar o `.env` (edite-o depois).
- [ ] Rodar `./scripts/02_install_alpine_deps.sh`.
- [ ] Iniciar o Docker (Postgres) com `./scripts/05_docker_management.sh up`.
- [ ] Rodar `./scripts/04_register_lights.py` para popular o banco.
- [ ] Registrar as cronjobs (usando o `crontab_template.txt`).
- [ ] Gravar o Firmware (`firmware/wemos_light.ino`) nas placas Wemos D1/ESP8266.

## 3. To-Do (Melhorias Futuras) 🛠️
- Criar script ou serviço OpenRC (Alpine) para manter o Bot, Web API e Solar Worker sempre rodando (Daemon).
- Adicionar sensor LDR no ESP para um modo "Fail-Safe" de acendimento caso a API ou a internet do Raspberry caia permanentemente.
