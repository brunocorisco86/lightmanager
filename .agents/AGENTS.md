# Light Manager Workspace Rules

Estas regras se aplicam a todas as interações e modificações no espaço de trabalho do **Light Manager**.

## 🌐 Ambiente de Produção
* O ambiente de produção está localizado na LAN e é acessível via SSH com o alias `ssh alpine`.
* O diretório base no servidor de produção é `/home/bruno/lightmanager`.
* Ao realizar implantações ou correções, certifique-se de instruir o usuário ou fornecer comandos para aplicar as mudanças em `ssh alpine`.
* **Fluxo de Deploy:** Prefira utilizar o fluxo de Git (commits locais, push e `git pull` em produção) em vez de cópia direta via `scp` ou `rsync` para transferir códigos para o servidor Alpine.

## 🕒 Fuso Horário e Registro
* Toda lógica de tempo e agendamento deve usar explicitamente o fuso horário de Brasília (GMT-3), correspondente a `America/Sao_Paulo` (ou `timezone(timedelta(hours=-3))`).
* O banco de dados PostgreSQL deve utilizar o tipo de dados `TIMESTAMPTZ` para armazenar registros de data/hora para garantir integridade.

## 🔌 Lógica de Hardware (ESP8266 Wemos D1 R1)
* Os relés controlados pelo Wemos operam em lógica **Active Low** (acionamento enviando sinal lógico `LOW`/`0`, e desligamento com `HIGH`/`1`).
* O Wemos tem watchdog de rede local independente configurado no firmware (`wemos_light.ino`).

## ⚙️ Manutenção de Serviços
* Os serviços em execução (API, Bot Telegram, Solar Worker) são gerenciados via scripts sob a pasta `scripts/`.
* Sempre execute `bash scripts/restart_<servico>.sh` correspondente após alterar qualquer código fonte.
* O bot do Telegram deve ser executado com o ambiente virtual `.venv` explicitamente ativo.
* Certifique-se de atualizar o `crontab_template.txt` se novos watchdogs ou scripts agendados forem criados, e aplique com `crontab crontab_template.txt` no Alpine.

## 🧪 Testes de Integridade
* Sempre rode `./run_tests.sh` localmente usando o PostgreSQL do `docker-compose.yml` para validar novas alterações e evitar regressões.
