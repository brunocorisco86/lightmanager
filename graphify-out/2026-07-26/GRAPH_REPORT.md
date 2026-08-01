# Graph Report - 9_LIGHT_MANAGER  (2026-07-26)

## Corpus Check
- 73 files · ~40,791 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 444 nodes · 521 edges · 67 communities (38 shown, 29 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e9b02cb6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Diário de Alterações (Changelog) - 21/06/2026
- main.py
- solar_worker.py
- script.js
- bot.py
- test_housekeeping.py
- ⚡ Comandos Úteis e Operação em Produção
- Light Manager
- TestSolarWorkerPerformance
- log_analyzer.py
- TestAutomationImprovements
- Light Manager Workspace Rules
- 📦 Configuração de Backup: Cloudflare R2
- test_auth.py
- ⚡ Fluxo de Deploy em Produção
- 3. To-Do (Melhorias Futuras) 🛠️
- backup_r2.sh
- Stack do Sistema - Light Manager
- test_bot_integrity.py
- test_command_reliability.py
- ⚡ Fluxo de Trabalho do Agente
- test_timezone.py
- tariff_sync.py
- weather_offset_sync.py
- test_api.py
- test_backup.py
- test_web_config.py
- 05_register_lights.py
- manage_users.py
- run_tests.sh
- 07_test_mqtt_commands.sh
- 08_flash_wemos.sh
- internet_watchdog.sh
- graphify.md
- graphify.md
- generate_daily.sh script
- 00_setup_python.sh
- 01_setup_env.sh
- 02_install_alpine_deps.sh
- 03_setup_mosquitto.sh
- 04_docker_management.sh
- 06_monitor_mqtt.sh
- entrypoint.sh
- desligar_frente.sh
- desligar_fundos.sh
- ligar_frente.sh
- ligar_fundos.sh
- network_watchdog.sh
- restart_api.sh
- restart_bot.sh
- restart_solar.sh
- setup.sh
- update_hosts.sh
- What You Must Do When Invoked
- graphify reference: extra exports and benchmark
- graphify reference: query, path, explain
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- extraction-spec.md

## God Nodes (most connected - your core abstractions)
1. `get_db_conn()` - 13 edges
2. `release_db_conn()` - 13 edges
3. `What You Must Do When Invoked` - 12 edges
4. `TestSolarWorkerPerformance` - 10 edges
5. `/graphify` - 10 edges
6. `send_telegram_message()` - 9 edges
7. `Diário de Alterações (Changelog) - 21/06/2026` - 9 edges
8. `check_auth()` - 8 edges
9. `get_light_points()` - 8 edges
10. `Light Manager Workspace Rules` - 8 edges

## Surprising Connections (you probably didn't know these)
- `test_prune_database_dry_run()` --calls--> `prune_database()`  [EXTRACTED]
  tests/test_housekeeping.py → scripts/housekeeping.py
- `test_prune_database_execution()` --calls--> `prune_database()`  [EXTRACTED]
  tests/test_housekeeping.py → scripts/housekeeping.py
- `test_prune_logs()` --calls--> `prune_logs()`  [EXTRACTED]
  tests/test_housekeeping.py → scripts/housekeeping.py
- `test_check_mosquitto_health()` --calls--> `check_mosquitto_health()`  [EXTRACTED]
  tests/test_housekeeping.py → scripts/housekeeping.py
- `test_send_telegram_message_failure()` --calls--> `send_telegram_message()`  [EXTRACTED]
  tests/test_telegram.py → scripts/solar_worker.py

## Import Cycles
- None detected.

## Communities (67 total, 29 thin omitted)

### Community 0 - "Diário de Alterações (Changelog) - 21/06/2026"
Cohesion: 0.05
Nodes (37): 🔍 1. Problemas e Solicitações, 🔍 1. Problemas Identificados (Erros em Produção), 1. Refatoração do Watchdog do Bot do Telegram, 2. Criação do Watchdog Local de Firmware (Resiliência do Wemos), 🛠️ 2. Melhorias e Correções Implementadas, 🛠️ 2. Resumo de Execução em Produção, 3. Desenvolvimento do Relatório Diário de Consumo via Telegram, ⛅ 3. Implementações do Dia 22/06/2026 (Sincronização Meteorológica) (+29 more)

### Community 1 - "main.py"
Cohesion: 0.17
Nodes (21): BaseModel, check_password(), CommandRequest, create_point(), delete_point(), get_consumption_history(), get_db_conn(), get_db_pool() (+13 more)

### Community 2 - "solar_worker.py"
Cohesion: 0.14
Nodes (22): fetch_sun_data_with_retry(), get_db_conn(), get_db_pool(), get_today_sun_data(), log_event_to_db(), on_message(), Salva um evento de estado no banco de dados com fonte e timestamp correto., Realiza a virada de dia virtual para fracionar o consumo de luzes que permanecem (+14 more)

### Community 3 - "script.js"
Cohesion: 0.18
Nodes (15): appendLogLine(), createNewPoint(), deletePoint(), fetchData(), loadCharts(), loadConfigList(), loadLogs(), loadMonthlyStats() (+7 more)

### Community 4 - "bot.py"
Cohesion: 0.26
Nodes (16): check_auth(), cmd_desliga(), cmd_liga(), cmd_relatorio(), cmd_start(), cmd_status(), execute_light_command(), get_consumption_report() (+8 more)

### Community 5 - "test_housekeeping.py"
Cohesion: 0.24
Nodes (13): check_mosquitto_health(), get_db_connection(), main(), prune_database(), prune_logs(), Verifica e reporta a integridade do diretório de dados e log do Mosquitto., Tenta conectar ao PostgreSQL usando variáveis de ambiente do .env., Pruna os eventos na tabela light_events mais antigos que N dias. (+5 more)

### Community 6 - "⚡ Comandos Úteis e Operação em Produção"
Cohesion: 0.17
Nodes (11): 1. Status Geral dos Serviços, 2. Reiniciar Serviços (Scripts de Autocura), 3. Visualizar Logs em Tempo Real, 4. Recarregar o Agendador Crontab, 5. Gestão de Usuários Administrativos, 🧪 Ambiente de Desenvolvimento & Testes Locais, 🌐 Ambiente de Produção (`ssh alpine`), 🛠️ Arquitetura do Sistema (+3 more)

### Community 7 - "Light Manager"
Cohesion: 0.18
Nodes (10): 🛠️ Arquitetura, 🧪 Como Rodar a Suíte de Testes Localmente, 🚀 Funcionalidades, ⚙️ Funcionalidades de Resiliência de Automação, ⚙️ Gestão e Manutenção, Light Manager, 🛡️ Mecanismos de Confiabilidade & Testes Locais, 🚀 Operação em Produção (Alpine Linux) (+2 more)

### Community 9 - "log_analyzer.py"
Cohesion: 0.29
Nodes (9): clean_timestamp(), extract_errors(), get_ai_summary(), main(), Envia uma mensagem de texto pelo bot do Telegram com tratamento de Rate-Limiting, Remove timestamps e datas da linha para agrupar erros repetidos., Lê todos os logs e extrai erros consolidados desduplicados., Envia os erros para a API do Gemini e obtém o resumo. (+1 more)

### Community 10 - "TestAutomationImprovements"
Cohesion: 0.27
Nodes (4): Valida se o manual_override é limpo no banco ao bater o minuto do gatilho solar., Valida se os horários de fallback enviados ao Wemos se ajustam aos offsets corre, Verifica se o manual_override ativa o estado desejado forçado independentemente, TestAutomationImprovements

### Community 12 - "Light Manager Workspace Rules"
Cohesion: 0.22
Nodes (8): 🌐 Ambiente de Produção, 🕒 Fuso Horário e Registro, ⚡ Gestão de Consumo e Tarifas, 🛡️ Guardrails & Resiliência, Light Manager Workspace Rules, 🔌 Lógica de Hardware (ESP8266 Wemos D1 R1), ⚙️ Manutenção de Serviços, 🧪 Testes de Integridade

### Community 13 - "📦 Configuração de Backup: Cloudflare R2"
Cohesion: 0.22
Nodes (8): 1. Configuração no Painel Cloudflare, 2.1 Atualizar o `.env`, 2.2 Dependências, 2. Configuração no Servidor (Local), 3. Execução e Teste, 4. Agendamento (Crontab), 5. Política de Retenção e Custos (Free Tier), 📦 Configuração de Backup: Cloudflare R2

### Community 14 - "test_auth.py"
Cohesion: 0.25
Nodes (8): get_db_connection(), Valida login com credenciais corretas, Valida falha com senha incorreta, Valida falha com usuário inexistente, setup_test_user(), test_login_success(), test_login_user_not_found(), test_login_wrong_password()

### Community 15 - "⚡ Fluxo de Deploy em Produção"
Cohesion: 0.25
Nodes (7): 1. Validação de Integridade Local, 2. Versionamento e Push, 3. Sincronização em Produção (Pull), 4. Recarregamento de Serviços e Cron, 5. Auditoria de Logs pós-boot, ⚡ Fluxo de Deploy em Produção, Skill: Git Deployer (git_deployer)

### Community 16 - "3. To-Do (Melhorias Futuras) 🛠️"
Cohesion: 0.25
Nodes (7): 1. Concluído ✅, 2. Next Steps (Para Comissionamento) 🚧, 3. To-Do (Melhorias Futuras) 🛠️, 🤖 Bot Telegram, ⚙️ Integração & Resiliência, Light Manager - Roadmap & Next Steps, 📊 Painel & Relatórios (Frontend/Backend)

### Community 17 - "backup_r2.sh"
Cohesion: 0.25
Nodes (7): RCLONE_CONFIG_R2_ACCESS_KEY_ID, RCLONE_CONFIG_R2_ACL, RCLONE_CONFIG_R2_ENDPOINT, RCLONE_CONFIG_R2_PROVIDER, RCLONE_CONFIG_R2_SECRET_ACCESS_KEY, RCLONE_CONFIG_R2_TYPE, backup_r2.sh script

### Community 18 - "Stack do Sistema - Light Manager"
Cohesion: 0.29
Nodes (6): Arquitetura e Hardware, Infraestrutura de Backups, Lógica e Automação (Python 3.11+), Persistência de Dados, Software e Comunicação, Stack do Sistema - Light Manager

### Community 19 - "test_bot_integrity.py"
Cohesion: 0.29
Nodes (6): Valida se as bibliotecas críticas do bot estão instaladas., Verifica se as variáveis mínimas do bot existem no .env, Verifica se o arquivo bot.py não tem erros de sintaxe e pode ser carregado., test_bot_dependencies(), test_bot_env_vars(), test_bot_syntax()

### Community 20 - "test_command_reliability.py"
Cohesion: 0.29
Nodes (6): Valida se o comando é enviado com sucesso via API e se o MQTT está conectado., Valida rejeição de payloads malformados, Valida se a API aguenta múltiplos comandos rápidos sem travar o loop MQTT, test_command_invalid_payload(), test_command_mqtt_qos_delivery(), test_rapid_commands()

### Community 21 - "⚡ Fluxo de Trabalho do Agente"
Cohesion: 0.33
Nodes (5): 1. Verificação Prévia de Hardware, 2. Executar o Script de Flash, 3. Validação de Rede e Comunicação MQTT, ⚡ Fluxo de Trabalho do Agente, Skill: Gravador de Firmware Embarcado (embedded_flasher)

### Community 22 - "test_timezone.py"
Cohesion: 0.47
Nodes (4): get_db_connection(), Valida se o banco de dados está processando e retornando TIMESTAMPTZ corretament, set_tz_config(), test_db_timezone_integrity()

### Community 23 - "tariff_sync.py"
Cohesion: 0.70
Nodes (4): create_table_if_not_exists(), get_csv_url(), get_db_connection(), sync()

### Community 25 - "test_api.py"
Cohesion: 0.40
Nodes (4): Testa se a API responde corretamente com formatted=0 (ISO 8601).     Isso valida, Valida os parâmetros do request_parameters.md., test_sunrise_sunset_api_iso_format(), test_sunrise_sunset_api_parameters()

### Community 26 - "test_backup.py"
Cohesion: 0.40
Nodes (4): Valida se as dependências do script de backup estão presentes no sistema., Garante que todas as variáveis necessárias para o backup no R2 estão no .env, test_backup_script_requirements(), test_r2_env_vars()

### Community 27 - "test_web_config.py"
Cohesion: 0.60
Nodes (3): get_db_connection(), setup_db(), test_solar_history_endpoint()

### Community 28 - "05_register_lights.py"
Cohesion: 0.83
Nodes (3): get_db_connection(), init_db(), register_point()

### Community 29 - "manage_users.py"
Cohesion: 0.83
Nodes (3): create_user(), get_db_connection(), init_users_table()

### Community 58 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 59 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 60 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 61 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 62 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 63 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **144 isolated node(s):** `generate_daily.sh script`, `run_tests.sh script`, `PYTHONPATH`, `00_setup_python.sh script`, `01_setup_env.sh script` (+139 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `generate_daily.sh script`, `run_tests.sh script`, `PYTHONPATH` to the rest of the system?**
  _144 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Diário de Alterações (Changelog) - 21/06/2026` be split into smaller, more focused modules?**
  _Cohesion score 0.05263157894736842 - nodes in this community are weakly interconnected._
- **Should `solar_worker.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13846153846153847 - nodes in this community are weakly interconnected._
- **Should `What You Must Do When Invoked` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._