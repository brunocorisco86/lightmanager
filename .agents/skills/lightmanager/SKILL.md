---
name: lightmanager
description: Manage, deploy, test, and debug the Light Manager smart outdoor lighting system, both locally and in the production environment (accessible via ssh alpine).
---

# Light Manager - Guia de Operação e Desenvolvimento

Este guia serve como a base de conhecimento (Skill) do **Light Manager**, um sistema minimalista e resiliente de automação de iluminação externa residencial projetado para rodar em um Raspberry Pi 3B com Alpine Linux (ambiente de produção) e integrado com Wemos D1 R1 (ESP8266) via MQTT (Mosquitto) e PostgreSQL.

---

## 🌐 Ambiente de Produção (`ssh alpine`)

O ambiente de produção reside na rede local e é diretamente acessível por SSH através do alias:
```bash
ssh alpine
```

* **Diretório de Produção:** `/home/bruno/lightmanager`
* **Usuário:** `bruno`
* **SO:** Alpine Linux
* **Banco de Dados:** PostgreSQL 15+ (rodando nativamente ou via Docker)
* **Broker MQTT:** Mosquitto (porta padrão 1883)

---

## 🛠️ Arquitetura do Sistema

O Light Manager é composto pelos seguintes subcomponentes e fluxos de execução:

1. **Firmware Wemos (`firmware/wemos_light/wemos_light.ino`):**
   - Roda em um ESP8266 com relé de 2 canais (Active Low).
   - Ouve tópicos MQTT para ligar/desligar luzes de forma incondicional.
   - Envia um heartbeat de status a cada 60 segundos.
   - Possui um watchdog de autocura local: reinicia a placa (`ESP.restart()`) se perder conexão WiFi ou MQTT por mais de 10 minutos.

2. **Web API (`web_api/main.py`):**
   - Backend escrito em **FastAPI** (Python 3.12).
   - Roda sob Uvicorn. Porta configurável via `.env` (acessada localmente ou redirecionada).
   - Gerencia pontos de iluminação, fuso horário, usuários, histórico solar e autenticação segura via BCrypt.

3. **Telegram Bot (`bot/bot.py`):**
   - Baseado na biblioteca **Aiogram 3**.
   - Opera via **Long Polling** recebendo e enviando comandos de controle: `/status`, `/liga`, `/desliga`.

4. **Solar Worker (`scripts/solar_worker.py`):**
   - Calcula cicladamente o horário do nascer/pôr do sol baseado nas coordenadas geográficas e offsets.
   - Envia de forma redundante (com QoS 1 e Retained Flags) os comandos MQTT para o Wemos nos horários calculados e como reforço a cada virada de hora.
   - Monitora se o Wemos está online 5 minutos antes do pôr/nascer do sol. Se inativo por >3 min, envia um `🚨 ALERTA DE SAÚDE EMBARCADO` via Telegram.

5. **Weather Sync (`scripts/weather_offset_sync.py`):**
   - Sincroniza dados climáticos com a API Open-Meteo duas vezes ao dia (05:00 e 17:00).
   - Executa interpolação linear dos offsets (desvios de tempo) baseando-se na cobertura de nuvens (`cloud_cover`):
     - 0% nuvens $\implies$ Ligar: +10 min / Desligar: -10 min
     - 100% nuvens $\implies$ Ligar: -10 min / Desligar: +10 min

6. **Relatórios Diários (`reports/generate_daily.py`):**
   - Executa às 23:55 via cron. Calcula tempo ativo e consumo de energia em kWh das lâmpadas (baseado no `power_w` no PostgreSQL). Envia o relatório final ao Telegram.

7. **Backups Cloud (`scripts/backup_r2.sh`):**
   - Cria dump do banco PostgreSQL e copia no bucket do Cloudflare R2 usando `rclone`.

---

## ⚡ Comandos Úteis e Operação em Produção

Após conectar via `ssh alpine`, use estes comandos para gerenciar o Light Manager:

### 1. Status Geral dos Serviços
Verifique se a API, o Bot do Telegram e o Solar Worker estão rodando:
```bash
pgrep -af python
```

### 2. Reiniciar Serviços (Scripts de Autocura)
```bash
# Reiniciar todos os serviços de uma vez
bash scripts/restart_api.sh && bash scripts/restart_solar.sh && bash scripts/restart_bot.sh

# Scripts individuais:
bash scripts/restart_api.sh
bash scripts/restart_solar.sh
bash scripts/restart_bot.sh
```

### 3. Visualizar Logs em Tempo Real
```bash
# Monitorar todos os logs ao mesmo tempo
tail -f logs/*.log

# Logs individuais:
tail -f logs/api.log        # API FastAPI
tail -f logs/solar.log      # Solar Worker
tail -f logs/bot.log        # Telegram Bot
tail -f logs/watchdog.log   # Watchdog de rede
tail -f logs/cron.log       # Erros e saídas do cron
```

### 4. Recarregar o Agendador Crontab
Sempre que fizer alterações no [crontab_template.txt](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/crontab_template.txt), aplique-as:
```bash
crontab crontab_template.txt
```

### 5. Gestão de Usuários Administrativos
Adicionar ou redefinir a senha de um usuário administrativo para a Interface Web:
```bash
python3 scripts/manage_users.py
```

---

## 🧪 Ambiente de Desenvolvimento & Testes Locais

Para simular o ambiente e testar novas funcionalidades no repositório local:

1. **Subir a infraestrutura (PostgreSQL de testes)**:
   ```bash
   docker-compose up -d
   ```

2. **Inicializar a base de dados de testes**:
   ```bash
   .venv/bin/python3 -c "import importlib; rl = importlib.import_module('scripts.05_register_lights'); rl.init_db(); import scripts.manage_users as mu; mu.init_users_table()"
   ```

3. **Rodar a suíte de testes (27 testes de integração/unitários)**:
   ```bash
   ./run_tests.sh
   ```
   *Nota: O script utiliza o arquivo `.env.test` e pula de forma limpa testes de componentes ausentes (ex: `rclone` ou `docker` fora do PATH).*

---

## ⚠️ Regras Cruciais de Desenvolvimento

* **Fuso Horário:** Use sempre `America/Sao_Paulo` (GMT-3) para todas as transações, logs e registros de banco de dados (`TIMESTAMPTZ` no PostgreSQL).
* **Watchdogs:** Os watchdogs rodam a cada 15 minutos via cron. Qualquer serviço Python deve escrever logs de status claros e ser reiniciável de forma idempotente via scripts em `scripts/restart_*.sh`.
* **Hardware Reconnect:** O ESP8266 Wemos D1 R1 deve enviar mensagens em tópicos MQTT específicos. Lembre-se de que o relé físico é **Active Low** (acionamento enviando nível lógico `LOW`).
* **Segurança:** Todas as rotas administrativas devem exigir autenticação robusta (BCrypt). Nunca guarde senhas em texto plano.
* **Fluxo de Deploy (Git vs. SCP):** Prefira utilizar sempre o fluxo do Git (commits locais, push para repositório remoto e `git pull` na máquina de produção via `ssh alpine`) para implantar atualizações em vez de comandos diretos de cópia como `scp` ou `rsync`.
