# Graph Report - 9_LIGHT_MANAGER  (2026-09-15)

## Corpus Check
- 90 files · ~55,681 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1317 nodes · 2869 edges · 100 communities (62 shown, 34 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 116 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `20a42574`
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
- bn
- log_analyzer.py
- TestAutomationImprovements
- test_web_api.py
- Light Manager Workspace Rules
- 📦 Configuração de Backup: Cloudflare R2
- an
- ⚡ Fluxo de Deploy em Produção
- Light Manager - Roadmap & Next Steps
- backup_r2.sh
- Stack do Sistema - Light Manager
- test_bot_integrity.py
- chart.min.js
- ⚡ 2. Fluxo ESP32-C3 SuperMini (RISC-V + Radar LD2420)
- test_timezone.py
- tariff_sync.py
- weather_offset_sync.py
- test_api.py
- test_backup.py
- o
- 05_register_lights.py
- manage_users.py
- run_tests.sh
- 07_test_mqtt_commands.sh
- 08_flash_wemos.sh
- internet_watchdog.sh
- rules/graphify.md
- workflows/graphify.md
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
- solar_scraper.py
- run_monthly_report_flow
- fetch_solar_forecast
- tn
- n
- .getDataset
- zt
- s
- inRange
- va
- ns
- ._resolveElementOptions
- d
- beforeUpdate
- .add
- no
- 09_flash_esp32c3.sh
- register_muro_point.py
- .getContext
- ca
- b
- l
- .getUserBounds
- updateElements
- ☀️ 1. Resumo das Etapas Implementadas (Roadmap Solar)
- getPixelForValue
- 🔍 1. Problemas e Solicitações
- Diário de Alterações (Changelog) - 01/08/2026 (Roadmap Fotovoltaico Completo)
- ⚡ 5. Implementações do Dia 24/06/2026 (Time Sync Híbrido, Rollover e Tarifas ANEEL)
- 🧠 8. Implementações do Dia 12/07/2026 (Housekeeping, Resiliência de DNS Unbound e Rate-limiting no Telegram)
- 🔍 1. Problemas Identificados (Erros em Produção)
- 🛠️ 2. Melhorias e Correções Implementadas
- 💡 4. Implementações do Dia 23/06/2026 (Consumo e Resiliência)

## God Nodes (most connected - your core abstractions)
1. `an()` - 61 edges
2. `ns()` - 55 edges
3. `s()` - 42 edges
4. `o()` - 40 edges
5. `a()` - 38 edges
6. `n()` - 37 edges
7. `no` - 35 edges
8. `l()` - 32 edges
9. `d()` - 31 edges
10. `va` - 30 edges

## Surprising Connections (you probably didn't know these)
- `test_prune_database_preserves_data()` --calls--> `prune_database()`  [EXTRACTED]
  tests/test_housekeeping.py → scripts/housekeeping.py
- `test_prune_logs()` --calls--> `prune_logs()`  [EXTRACTED]
  tests/test_housekeeping.py → scripts/housekeeping.py
- `test_check_mosquitto_health()` --calls--> `check_mosquitto_health()`  [EXTRACTED]
  tests/test_housekeeping.py → scripts/housekeeping.py
- `test_solar_ai_expert_no_key()` --calls--> `analyze_solar_anomaly_with_ai()`  [EXTRACTED]
  tests/test_solar_ai_expert.py → scripts/solar_ai_expert.py
- `test_calculate_system_efficiency_factor_default()` --calls--> `calculate_system_efficiency_factor()`  [EXTRACTED]
  tests/test_solar_forecast.py → scripts/solar_forecast.py

## Import Cycles
- None detected.

## Communities (100 total, 34 thin omitted)

### Community 0 - "Diário de Alterações (Changelog) - 21/06/2026"
Cohesion: 0.22
Nodes (9): ⛅ 3. Implementações do Dia 22/06/2026 (Sincronização Meteorológica), ⚡ 6. Implementações do Dia 25/06/2026 (Persistência de Override Manual e Correção de Oscilação de Fallback), 🎙️ 7. Implementações do Dia 11/07/2026 (Comandos de Voz via Gemini API e Reorganização de Documentos), 🔄 Correção de Oscilação ao Ligar (Conflito de Fallback e Trigger Solar), Diário de Alterações (Changelog) - 21/06/2026, 💾 Persistência de Decisão (Override Manual), 🗣️ Reconhecimento de Comandos de Voz via Telegram Bot, 📂 Reorganização e Limpeza de Documentos (Eliminação de Redundâncias) (+1 more)

### Community 1 - "main.py"
Cohesion: 0.07
Nodes (53): BaseModel, delete, get, post, put, get_db_connection(), fixture, Valida login com credenciais corretas (+45 more)

### Community 2 - "solar_worker.py"
Cohesion: 0.07
Nodes (38): calculate_daily_summary(), fetch_daily_solar_data(), generate_solar_chart_png(), get_db_conn(), Gera o gráfico da curva sino de potência solar fotovoltaica usando Matplotlib…, Gera e envia o relatório diário de produção solar fotovoltaica para o Telegram., Busca todas as entradas de telemetria solar registradas no banco para o dia…, Calcula os indicadores resumidos (KPIs) da geração do dia. (+30 more)

### Community 3 - "script.js"
Cohesion: 0.15
Nodes (19): appendLogLine(), createNewPoint(), deletePoint(), fetchData(), loadCharts(), loadConfigList(), loadLogs(), loadMonthlyStats() (+11 more)

### Community 4 - "bot.py"
Cohesion: 0.24
Nodes (18): check_auth(), cmd_desliga(), cmd_liga(), cmd_relatorio(), cmd_solar(), cmd_start(), cmd_status(), execute_light_command() (+10 more)

### Community 5 - "test_housekeeping.py"
Cohesion: 0.24
Nodes (12): check_mosquitto_health(), get_db_connection(), main(), prune_database(), prune_logs(), Tenta conectar ao PostgreSQL usando variáveis de ambiente do .env., Preserva integralmente todos os registros de tabelas no banco de dados…, Roda logrotate e deleta arquivos de log rotacionados/comprimidos mais antigos… (+4 more)

### Community 6 - "⚡ Comandos Úteis e Operação em Produção"
Cohesion: 0.17
Nodes (11): 1. Status Geral dos Serviços, 2. Reiniciar Serviços (Scripts de Autocura), 3. Visualizar Logs em Tempo Real, 4. Recarregar o Agendador Crontab, 5. Gestão de Usuários Administrativos, 🧪 Ambiente de Desenvolvimento & Testes Locais, 🌐 Ambiente de Produção (`ssh alpine`), 🛠️ Arquitetura do Sistema (+3 more)

### Community 7 - "Light Manager"
Cohesion: 0.18
Nodes (10): 🛠️ Arquitetura, 🧪 Como Rodar a Suíte de Testes Localmente, 🚀 Funcionalidades, ⚙️ Funcionalidades de Resiliência de Automação, ⚙️ Gestão e Manutenção, Light Manager, 🛡️ Mecanismos de Confiabilidade & Testes Locais, 🚀 Operação em Produção (Alpine Linux) (+2 more)

### Community 8 - "bn"
Cohesion: 0.16
Nodes (5): bn, on(), pn(), xn(), Ye()

### Community 9 - "log_analyzer.py"
Cohesion: 0.29
Nodes (9): clean_timestamp(), extract_errors(), get_ai_summary(), main(), Envia uma mensagem de texto pelo bot do Telegram com tratamento de Rate-…, Remove timestamps e datas da linha para agrupar erros repetidos., Lê todos os logs e extrai erros consolidados desduplicados., Envia os erros para a API do Gemini e obtém o resumo. (+1 more)

### Community 10 - "TestAutomationImprovements"
Cohesion: 0.27
Nodes (5): patch, Valida se o manual_override é limpo no banco ao bater o minuto do gatilho solar., Valida se os horários de fallback enviados ao Wemos se ajustam aos offsets…, Verifica se o manual_override ativa o estado desejado forçado independentemente…, TestAutomationImprovements

### Community 11 - "test_web_api.py"
Cohesion: 0.28
Nodes (12): patch, test_get_consumption_history_success(), test_get_history_success(), test_get_muro_night_stats_success(), test_get_solar_generation_curve_success(), test_get_status_db_error(), test_get_status_success(), test_get_sun_times_cached() (+4 more)

### Community 12 - "Light Manager Workspace Rules"
Cohesion: 0.22
Nodes (8): 🌐 Ambiente de Produção, 🕒 Fuso Horário e Registro, ⚡ Gestão de Consumo e Tarifas, 🛡️ Guardrails & Resiliência, Light Manager Workspace Rules, 🔌 Lógica de Hardware (ESP8266 Wemos D1 R1), ⚙️ Manutenção de Serviços, 🧪 Testes de Integridade

### Community 13 - "📦 Configuração de Backup: Cloudflare R2"
Cohesion: 0.22
Nodes (8): 1. Configuração no Painel Cloudflare, 2.1 Atualizar o `.env`, 2.2 Dependências, 2. Configuração no Servidor (Local), 3. Execução e Teste, 4. Agendamento (Crontab), 5. Política de Retenção e Custos (Free Tier), 📦 Configuração de Backup: Cloudflare R2

### Community 14 - "an"
Cohesion: 0.05
Nodes (21): addBox(), afterDatasetsUpdate(), an(), configure(), ct(), fs(), generateLabels(), ke() (+13 more)

### Community 15 - "⚡ Fluxo de Deploy em Produção"
Cohesion: 0.22
Nodes (8): 1. Validação de Integridade Local, 2. Versionamento e Push, 3. Sincronização em Produção (Pull), 4. Recarregamento de Serviços e Cron, 5. Auditoria de Logs pós-boot, 6. Teste Obrigatório no Telegram pós-deploy, ⚡ Fluxo de Deploy em Produção, Skill: Git Deployer (git_deployer)

### Community 16 - "Light Manager - Roadmap & Next Steps"
Cohesion: 0.22
Nodes (8): 1. Concluído ✅, 2. Next Steps (Para Comissionamento) 🚧, 3. To-Do (Melhorias Futuras) 🛠️, 4. Roadmap Fotovoltaico (Geração Solar) ☀️, 🤖 Bot Telegram, ⚙️ Integração & Resiliência, Light Manager - Roadmap & Next Steps, 📊 Painel & Relatórios (Frontend/Backend)

### Community 17 - "backup_r2.sh"
Cohesion: 0.25
Nodes (7): RCLONE_CONFIG_R2_ACCESS_KEY_ID, RCLONE_CONFIG_R2_ACL, RCLONE_CONFIG_R2_ENDPOINT, RCLONE_CONFIG_R2_PROVIDER, RCLONE_CONFIG_R2_SECRET_ACCESS_KEY, RCLONE_CONFIG_R2_TYPE, backup_r2.sh script

### Community 18 - "Stack do Sistema - Light Manager"
Cohesion: 0.29
Nodes (6): Arquitetura e Hardware, Infraestrutura de Backups, Lógica e Automação (Python 3.11+), Persistência de Dados, Software e Comunicação, Stack do Sistema - Light Manager

### Community 19 - "test_bot_integrity.py"
Cohesion: 0.29
Nodes (6): Valida se as bibliotecas críticas do bot estão instaladas., Verifica se as variáveis mínimas do bot existem no .env, Verifica se o arquivo bot.py não tem erros de sintaxe e pode ser carregado., test_bot_dependencies(), test_bot_env_vars(), test_bot_syntax()

### Community 20 - "chart.min.js"
Cohesion: 0.05
Nodes (13): destroy(), es(), getMaxOverflow(), Ie(), Jo(), ln(), Qi(), rn() (+5 more)

### Community 21 - "⚡ 2. Fluxo ESP32-C3 SuperMini (RISC-V + Radar LD2420)"
Cohesion: 0.29
Nodes (6): ⚡ 1. Fluxo Wemos D1 R1 (ESP8266), ⚡ 2. Fluxo ESP32-C3 SuperMini (RISC-V + Radar LD2420), Características de Hardware, Monitoramento Serial ao Vivo, Roteiro de Gravação, Skill: Gravador de Firmware Embarcado (embedded_flasher)

### Community 22 - "test_timezone.py"
Cohesion: 0.47
Nodes (4): get_db_connection(), Valida se o banco de dados está processando e retornando TIMESTAMPTZ…, set_tz_config(), test_db_timezone_integrity()

### Community 23 - "tariff_sync.py"
Cohesion: 0.70
Nodes (4): create_table_if_not_exists(), get_csv_url(), get_db_connection(), sync()

### Community 24 - "weather_offset_sync.py"
Cohesion: 0.33
Nodes (5): parametrize, get_db_connection(), main(), patch, test_weather_offset_sync()

### Community 25 - "test_api.py"
Cohesion: 0.40
Nodes (4): Testa se a API responde corretamente com formatted=0 (ISO 8601). Isso valida a…, Valida os parâmetros do request_parameters.md., test_sunrise_sunset_api_iso_format(), test_sunrise_sunset_api_parameters()

### Community 26 - "test_backup.py"
Cohesion: 0.40
Nodes (4): Valida se as dependências do script de backup estão presentes no sistema., Garante que todas as variáveis necessárias para o backup no R2 estão no .env, test_backup_script_requirements(), test_r2_env_vars()

### Community 27 - "o"
Cohesion: 0.14
Nodes (19): a(), aa(), ai(), cn(), dn(), draw(), gi(), hn() (+11 more)

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

### Community 67 - "solar_scraper.py"
Cohesion: 0.08
Nodes (44): analyze_solar_anomaly_with_ai(), Invoca o Agente Especialista Fotovoltaico (Gemini AI) para analisar a anomalia…, cache_working_ip(), check_solar_anomalies(), fetch_solar_telemetry(), find_ip_in_arp(), get_inverter_ip_hint(), get_inverter_mac() (+36 more)

### Community 68 - "run_monthly_report_flow"
Cohesion: 0.15
Nodes (21): fetch_monthly_solar_data(), generate_ai_monthly_consultant_report(), get_db_conn(), get_target_month_range(), get_tariff_rate(), Obtém a tarifa da concessionária (R$/kWh) gravada no DB ou parâmetro local., Gera o gráfico de barras mensal da geração diária (kWh) usando Matplotlib…, Comprime o contexto e invoca o Agente Consultor IA (Gemini API) para emitir… (+13 more)

### Community 69 - "fetch_solar_forecast"
Cohesion: 0.18
Nodes (14): calculate_system_efficiency_factor(), fetch_solar_forecast(), get_db_conn(), Consulta a API Open-Meteo Solar Forecast e retorna a previsão estimada de…, Calcula o fator dinâmico de conversão (kWh por MJ/m²) baseado no histórico…, check_abrupt_power_drop_and_rain(), Detecta queda abrupta de geração solar no horário de pico e cruza com a…, patch (+6 more)

### Community 70 - "tn"
Cohesion: 0.07
Nodes (8): addElements(), Cs, fe(), ks(), nn(), os(), sn, tn

### Community 71 - "n"
Cohesion: 0.06
Nodes (11): Do(), eo(), getLabelAndValue(), getLabelForValue(), jn, n(), ne(), numeric() (+3 more)

### Community 73 - "zt"
Cohesion: 0.07
Nodes (15): bt, color(), Ft(), Gt(), It(), jt(), kt(), mt() (+7 more)

### Community 74 - "s"
Cohesion: 0.09
Nodes (17): at(), beforeDraw(), bo, et(), getRange(), H(), hi(), s() (+9 more)

### Community 75 - "inRange"
Cohesion: 0.10
Nodes (25): ao(), average(), dataset(), getCenterPoint(), ho(), Hs, _i(), index() (+17 more)

### Community 76 - "va"
Cohesion: 0.07
Nodes (24): afterDraw(), afterEvent(), afterUpdate(), Ee(), f(), g(), gs(), ki() (+16 more)

### Community 77 - "ns"
Cohesion: 0.12
Nodes (3): As(), ns(), updateRangeFromParsed()

### Community 81 - ".add"
Cohesion: 0.67
Nodes (3): ei(), je(), ti()

### Community 82 - "no"
Cohesion: 0.06
Nodes (14): beforeLayout(), buildLookupTable(), En, Fo(), _generate(), getDecimalForValue(), _getTimestampsForTable(), init() (+6 more)

### Community 90 - ".getContext"
Cohesion: 0.39
Nodes (3): Bi(), Ci(), Fi()

### Community 91 - "ca"
Cohesion: 0.11
Nodes (20): beforeDatasetDraw(), beforeDatasetsDraw(), ca(), da(), e(), ea(), fa(), ga() (+12 more)

### Community 92 - "b"
Cohesion: 0.06
Nodes (13): b(), be(), ce(), de, dt(), ge(), he(), ls (+5 more)

### Community 93 - "l"
Cohesion: 0.15
Nodes (12): buildTicks(), Fn(), Gn(), go(), ii(), l(), parse(), parseArrayData() (+4 more)

### Community 100 - ".getUserBounds"
Cohesion: 0.13
Nodes (5): determineDataLimits(), getValueForPixel(), ko, pt(), xo

### Community 107 - "☀️ 1. Resumo das Etapas Implementadas (Roadmap Solar)"
Cohesion: 0.25
Nodes (8): ☀️ 1. Resumo das Etapas Implementadas (Roadmap Solar), 📈 Etapa 1: Relatório Pós-Pôr do Sol com Gráfico Matplotlib Headless, 🔮 Etapa 2: Previsão Solar via Open-Meteo & Calibração Dinâmica, 📊 Etapa 3: Curva Sino de Potência no Dashboard Frontend Web, 🚨 Etapa 4: Alertas de Anomalia + Agente IA Especialista em Elétrica Solar (Gemini API), 🌧️ Etapa 5: Alerta Preventivo de Chuva (Drop Solar + Open-Meteo), 📊 Etapa 6: Relatório Mensal Consolidado + Agente Consultor IA (Cron Dia 01 às 06:30h), 🚀 Resiliência de Scraping por Endereço MAC (Inversor Solar)

### Community 108 - "getPixelForValue"
Cohesion: 0.15
Nodes (10): Ae(), _calculateBarIndexPixels(), getPixelForTick(), getPixelForValue(), _getRuler(), _getStackCount(), _getStackIndex(), _getStacks() (+2 more)

### Community 109 - "🔍 1. Problemas e Solicitações"
Cohesion: 0.29
Nodes (6): 🔍 1. Problemas e Solicitações, 🛠️ 2. Resumo de Execução em Produção, 🛡️ Definição de Guardrails do Agente, Diário de Alterações (Changelog) - 19/07/2026, 💾 Mosquitto persistence & Desgaste de Cartão SD (Overhead de I/O), 🧹 Prunagem de Banco de Dados e Logs (Housekeeping)

### Community 111 - "Diário de Alterações (Changelog) - 01/08/2026 (Roadmap Fotovoltaico Completo)"
Cohesion: 0.40
Nodes (5): ⚡ 02/08/2026 - Correção de Oscilação de Luzes (Fuso Horário de Fallback MQTT BRT), 🧪 2. Validação & Deploy em Produção, 🛠️ Correções e Ajustes, 🐛 Diagnóstico do Problema (Luzes Piscando a Cada Minuto), Diário de Alterações (Changelog) - 01/08/2026 (Roadmap Fotovoltaico Completo)

### Community 112 - "⚡ 5. Implementações do Dia 24/06/2026 (Time Sync Híbrido, Rollover e Tarifas ANEEL)"
Cohesion: 0.40
Nodes (5): ⚡ 5. Implementações do Dia 24/06/2026 (Time Sync Híbrido, Rollover e Tarifas ANEEL), ⚡ Correção de Duração Truncada por Reforço Horário, 💰 Integração Tarifária e Financeira (ANEEL & Impostos), 🌙 Mecanismo de Virada de Dia (Rollover), ⏰ Sincronização de Tempo Híbrida (Remoção do NTP no Embarcado)

### Community 113 - "🧠 8. Implementações do Dia 12/07/2026 (Housekeeping, Resiliência de DNS Unbound e Rate-limiting no Telegram)"
Cohesion: 0.40
Nodes (5): 🧠 8. Implementações do Dia 12/07/2026 (Housekeeping, Resiliência de DNS Unbound e Rate-limiting no Telegram), 🤖 Análise e Notificação Inteligente de Erros (Gemini 2.5 Flash + Telegram), ☀️ Coleta e Scraping de Dados de Geração Solar (Inversor LAN 192.168.1.13), 🧹 Housekeeping de Logs (logrotate e copytruncate), 🌐 Watchdog Híbrido de Internet e DNS Local Unbound (Governança e Autorrecuperação)

### Community 114 - "🔍 1. Problemas Identificados (Erros em Produção)"
Cohesion: 0.50
Nodes (4): 🔍 1. Problemas Identificados (Erros em Produção), 🔌 Dispositivo Wemos Sem Comunicação (MQTT Timeout), 📅 Erros Críticos de Script Inexistente no Cron, 🤖 Telegram Bot Inativo

### Community 115 - "🛠️ 2. Melhorias e Correções Implementadas"
Cohesion: 0.50
Nodes (4): 1. Refatoração do Watchdog do Bot do Telegram, 2. Criação do Watchdog Local de Firmware (Resiliência do Wemos), 🛠️ 2. Melhorias e Correções Implementadas, 3. Desenvolvimento do Relatório Diário de Consumo via Telegram

### Community 116 - "💡 4. Implementações do Dia 23/06/2026 (Consumo e Resiliência)"
Cohesion: 0.50
Nodes (4): 💡 4. Implementações do Dia 23/06/2026 (Consumo e Resiliência), 🔌 Correção do Desligamento Precoce da Luz (Bug de Limite NTP), 🛡️ Fallback Local de Cronograma no Firmware (Wemos Offline), 📊 Registro de Duração e Consumo de Energia em kWh

## Knowledge Gaps
- **157 isolated node(s):** `generate_daily.sh script`, `run_tests.sh script`, `PYTHONPATH`, `00_setup_python.sh script`, `01_setup_env.sh script` (+152 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 374 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ns()` connect `ns` to `updateElements`, `tn`, `n`, `.getDataset`, `bn`, `va`, `._resolveElementOptions`, `an`, `beforeUpdate`, `no`, `chart.min.js`, `.getContext`, `o`, `l`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `an()` connect `an` to `tn`, `s`, `inRange`, `chart.min.js`, `.getContext`, `o`, `b`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `fetch_solar_forecast()` connect `fetch_solar_forecast` to `main.py`, `solar_worker.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `s()` (e.g. with `beforeUpdate()` and `da()`) actually correct?**
  _`s()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `o()` (e.g. with `ai()` and `da()`) actually correct?**
  _`o()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `a()` (e.g. with `ai()` and `cn()`) actually correct?**
  _`a()` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `generate_daily.sh script`, `run_tests.sh script`, `PYTHONPATH` to the rest of the system?**
  _157 weakly-connected nodes found - possible documentation gaps or missing edges._