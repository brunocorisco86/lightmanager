# Graph Report - 9_LIGHT_MANAGER  (2026-08-02)

## Corpus Check
- 87 files · ~54,334 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1299 nodes · 2933 edges · 102 communities (67 shown, 35 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 188 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bb7027e3`
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
- test_web_api.py
- Light Manager Workspace Rules
- 📦 Configuração de Backup: Cloudflare R2
- test_auth.py
- ⚡ Fluxo de Deploy em Produção
- 3. To-Do (Melhorias Futuras) 🛠️
- backup_r2.sh
- Stack do Sistema - Light Manager
- test_bot_integrity.py
- chart.min.js
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
- test_solar_scraper.py
- run_monthly_report_flow
- fetch_solar_forecast
- ☀️ 1. Resumo das Etapas Implementadas (Roadmap Solar)
- send_daily_solar_telegram_report
- analyze_solar_anomaly_with_ai
- zt
- s
- inRange
- va
- bn
- ns
- d
- eo
- Si
- no
- da
- .bindResponsiveEvents
- solar_scraper.py
- xa
- .getDataTimestamps
- send_telegram_message
- En
- .getContext
- fa
- de
- parse
- rs
- .isHorizontal
- .getLabels
- .getDataset
- analyze_solar_anomaly_with_ai
- ._resolveElementOptions
- beforeUpdate

## God Nodes (most connected - your core abstractions)
1. `va` - 73 edges
2. `an()` - 61 edges
3. `ns()` - 55 edges
4. `s()` - 53 edges
5. `o()` - 48 edges
6. `a()` - 47 edges
7. `l()` - 43 edges
8. `r()` - 39 edges
9. `n()` - 37 edges
10. `e()` - 32 edges

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

## Communities (102 total, 35 thin omitted)

### Community 0 - "Diário de Alterações (Changelog) - 21/06/2026"
Cohesion: 0.04
Nodes (47): 🔍 1. Problemas e Solicitações, 🔍 1. Problemas Identificados (Erros em Produção), 1. Refatoração do Watchdog do Bot do Telegram, ☀️ 1. Resumo das Etapas Implementadas (Roadmap Solar), 2. Criação do Watchdog Local de Firmware (Resiliência do Wemos), 🛠️ 2. Melhorias e Correções Implementadas, 🛠️ 2. Resumo de Execução em Produção, 🧪 2. Validação & Deploy em Produção (+39 more)

### Community 1 - "main.py"
Cohesion: 0.07
Nodes (52): BaseModel, delete, get, post, put, get_db_connection(), fixture, Valida login com credenciais corretas (+44 more)

### Community 2 - "solar_worker.py"
Cohesion: 0.26
Nodes (13): fetch_sun_data_with_retry(), get_db_conn(), get_db_pool(), get_today_sun_data(), log_event_to_db(), on_message(), Salva um evento de estado no banco de dados com fonte e timestamp correto., Realiza a virada de dia virtual para fracionar o consumo de luzes que permanecem (+5 more)

### Community 3 - "script.js"
Cohesion: 0.12
Nodes (24): at(), e(), ei(), je(), qe(), ti(), appendLogLine(), createNewPoint() (+16 more)

### Community 4 - "bot.py"
Cohesion: 0.24
Nodes (18): check_auth(), cmd_desliga(), cmd_liga(), cmd_relatorio(), cmd_solar(), cmd_start(), cmd_status(), execute_light_command() (+10 more)

### Community 5 - "test_housekeeping.py"
Cohesion: 0.24
Nodes (12): check_mosquitto_health(), get_db_connection(), main(), prune_database(), prune_logs(), Tenta conectar ao PostgreSQL usando variáveis de ambiente do .env., Preserva integralmente todos os registros de tabelas no banco de dados (PostgreS, Roda logrotate e deleta arquivos de log rotacionados/comprimidos mais antigos qu (+4 more)

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
Nodes (5): patch, Valida se o manual_override é limpo no banco ao bater o minuto do gatilho solar., Valida se os horários de fallback enviados ao Wemos se ajustam aos offsets corre, Verifica se o manual_override ativa o estado desejado forçado independentemente, TestAutomationImprovements

### Community 11 - "test_web_api.py"
Cohesion: 0.30
Nodes (11): patch, test_get_consumption_history_success(), test_get_history_success(), test_get_solar_generation_curve_success(), test_get_status_db_error(), test_get_status_success(), test_get_sun_times_cached(), test_get_sun_times_failure() (+3 more)

### Community 12 - "Light Manager Workspace Rules"
Cohesion: 0.22
Nodes (8): 🌐 Ambiente de Produção, 🕒 Fuso Horário e Registro, ⚡ Gestão de Consumo e Tarifas, 🛡️ Guardrails & Resiliência, Light Manager Workspace Rules, 🔌 Lógica de Hardware (ESP8266 Wemos D1 R1), ⚙️ Manutenção de Serviços, 🧪 Testes de Integridade

### Community 13 - "📦 Configuração de Backup: Cloudflare R2"
Cohesion: 0.22
Nodes (8): 1. Configuração no Painel Cloudflare, 2.1 Atualizar o `.env`, 2.2 Dependências, 2. Configuração no Servidor (Local), 3. Execução e Teste, 4. Agendamento (Crontab), 5. Política de Retenção e Custos (Free Tier), 📦 Configuração de Backup: Cloudflare R2

### Community 14 - "test_auth.py"
Cohesion: 0.06
Nodes (17): addBox(), afterDatasetsUpdate(), an(), configure(), generateLabels(), ke(), kn(), Mn() (+9 more)

### Community 15 - "⚡ Fluxo de Deploy em Produção"
Cohesion: 0.22
Nodes (8): 1. Validação de Integridade Local, 2. Versionamento e Push, 3. Sincronização em Produção (Pull), 4. Recarregamento de Serviços e Cron, 5. Auditoria de Logs pós-boot, 6. Teste Obrigatório no Telegram pós-deploy, ⚡ Fluxo de Deploy em Produção, Skill: Git Deployer (git_deployer)

### Community 16 - "3. To-Do (Melhorias Futuras) 🛠️"
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
Cohesion: 0.04
Nodes (20): be(), _calculateBarIndexPixels(), destroy(), es(), getPixelForTick(), getPixelForValue(), _getRuler(), _getStackCount() (+12 more)

### Community 21 - "⚡ Fluxo de Trabalho do Agente"
Cohesion: 0.33
Nodes (5): 1. Verificação Prévia de Hardware, 2. Executar o Script de Flash, 3. Validação de Rede e Comunicação MQTT, ⚡ Fluxo de Trabalho do Agente, Skill: Gravador de Firmware Embarcado (embedded_flasher)

### Community 22 - "test_timezone.py"
Cohesion: 0.47
Nodes (4): get_db_connection(), Valida se o banco de dados está processando e retornando TIMESTAMPTZ corretament, set_tz_config(), test_db_timezone_integrity()

### Community 23 - "tariff_sync.py"
Cohesion: 0.70
Nodes (4): create_table_if_not_exists(), get_csv_url(), get_db_connection(), sync()

### Community 24 - "weather_offset_sync.py"
Cohesion: 0.33
Nodes (5): parametrize, get_db_connection(), main(), patch, test_weather_offset_sync()

### Community 25 - "test_api.py"
Cohesion: 0.40
Nodes (4): Testa se a API responde corretamente com formatted=0 (ISO 8601).     Isso valida, Valida os parâmetros do request_parameters.md., test_sunrise_sunset_api_iso_format(), test_sunrise_sunset_api_parameters()

### Community 26 - "test_backup.py"
Cohesion: 0.40
Nodes (4): Valida se as dependências do script de backup estão presentes no sistema., Garante que todas as variáveis necessárias para o backup no R2 estão no .env, test_backup_script_requirements(), test_r2_env_vars()

### Community 27 - "test_web_config.py"
Cohesion: 0.10
Nodes (30): a(), aa(), cn(), determineDataLimits(), dn(), Fn(), gi(), Gn() (+22 more)

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

### Community 67 - "test_solar_scraper.py"
Cohesion: 0.17
Nodes (19): fetch_solar_telemetry(), parse_solar_csv(), publish_solar_mqtt(), Decodifica os 35 valores CSV retornados pelo endpoint status/status.php do inver, Solicita a telemetria do inversor via requisição HTTP POST.     Resolve o IP din, Persiste o registro de telemetria solar na tabela solar_generation., Publica os dados de geração solar nos tópicos MQTT correspondentes., Ciclo principal de coleta de telemetria solar:     1. Scraping via HTTP (POST st (+11 more)

### Community 68 - "run_monthly_report_flow"
Cohesion: 0.15
Nodes (21): fetch_monthly_solar_data(), generate_ai_monthly_consultant_report(), get_db_conn(), get_target_month_range(), get_tariff_rate(), Obtém a tarifa da concessionária (R$/kWh) gravada no DB ou parâmetro local., Gera o gráfico de barras mensal da geração diária (kWh) usando Matplotlib headle, Comprime o contexto e invoca o Agente Consultor IA (Gemini API) para emitir pare (+13 more)

### Community 69 - "fetch_solar_forecast"
Cohesion: 0.10
Nodes (27): calculate_system_efficiency_factor(), fetch_solar_forecast(), get_db_conn(), Consulta a API Open-Meteo Solar Forecast e retorna a previsão estimada de geraçã, Calcula o fator dinâmico de conversão (kWh por MJ/m²) baseado no histórico recen, check_abrupt_power_drop_and_rain(), Detecta queda abrupta de geração solar no horário de pico e cruza com a probabil, calculate_daily_summary() (+19 more)

### Community 70 - "☀️ 1. Resumo das Etapas Implementadas (Roadmap Solar)"
Cohesion: 0.07
Nodes (8): addElements(), Cs, fe(), ks(), nn(), os(), sn, tn

### Community 71 - "send_daily_solar_telegram_report"
Cohesion: 0.08
Nodes (9): _calculateBarValuePixels(), getBasePixel(), getLabelAndValue(), getLabelForValue(), getValueForPixel(), jn, resolveDataElementOptions(), updateElements() (+1 more)

### Community 72 - "analyze_solar_anomaly_with_ai"
Cohesion: 0.43
Nodes (7): check_solar_anomalies(), Verifica a ocorrência de anomalias no inversor solar e envia alertas no Telegram, test_check_solar_anomalies_high_temperature(), test_check_solar_anomalies_inverter_fault(), test_check_solar_anomalies_normal(), test_check_solar_anomalies_pv_asymmetry(), test_check_solar_anomalies_waiting_status_ignored()

### Community 73 - "zt"
Cohesion: 0.08
Nodes (13): bt, color(), Ft(), It(), kt(), mt(), qt(), _t() (+5 more)

### Community 74 - "s"
Cohesion: 0.08
Nodes (18): b(), bo, dt(), et(), H(), ia(), j(), ko (+10 more)

### Community 75 - "inRange"
Cohesion: 0.12
Nodes (25): ao(), average(), dataset(), getCenterPoint(), ho(), Hs, _i(), index() (+17 more)

### Community 76 - "va"
Cohesion: 0.14
Nodes (10): afterDraw(), afterEvent(), beforeLayout(), f(), qo(), ts(), update(), va (+2 more)

### Community 77 - "bn"
Cohesion: 0.14
Nodes (5): bn, pn(), un(), xn(), Ye()

### Community 78 - "ns"
Cohesion: 0.13
Nodes (3): As(), ns(), updateRangeFromParsed()

### Community 80 - "eo"
Cohesion: 0.18
Nodes (4): ca(), Do(), eo(), Oe()

### Community 81 - "Si"
Cohesion: 0.26
Nodes (9): Ee(), ki(), Le(), Oi(), p(), Si(), to(), wi() (+1 more)

### Community 83 - "da"
Cohesion: 0.14
Nodes (15): ai(), beforeDatasetDraw(), beforeDatasetsDraw(), beforeDraw(), da(), draw(), getMaxOverflow(), getRange() (+7 more)

### Community 84 - ".bindResponsiveEvents"
Cohesion: 0.17
Nodes (10): ct(), fs(), ge(), gs(), ms(), ps(), vs(), we() (+2 more)

### Community 85 - "solar_scraper.py"
Cohesion: 0.22
Nodes (13): cache_working_ip(), find_ip_in_arp(), get_inverter_ip_hint(), get_inverter_mac(), init_solar_db(), Resolve dinamicamente o IP do inversor solar com resiliência baseada em MAC Addr, Garante que a tabela solar_generation exista no banco PostgreSQL., Busca o IP correspondente ao MAC address informado na tabela ARP do sistema (/pr (+5 more)

### Community 86 - "xa"
Cohesion: 0.23
Nodes (3): afterUpdate(), g(), xa

### Community 87 - ".getDataTimestamps"
Cohesion: 0.21
Nodes (6): buildLookupTable(), _generate(), _getTimestampsForTable(), initOffsets(), lt(), nt()

### Community 88 - "send_telegram_message"
Cohesion: 0.26
Nodes (10): Envia uma notificação para o Telegram com tratamento de Rate-Limiting e retentat, send_telegram_message(), test_real_notification(), patch, Valida se a função de envio chama a URL correta do Telegram com o payload espera, Valida se a função trata erros de rede ou status sem quebrar o worker., Garante que nada é enviado se o token não estiver configurado., test_send_telegram_message_failure() (+2 more)

### Community 89 - "En"
Cohesion: 0.18
Nodes (3): En, Fo(), zo()

### Community 90 - ".getContext"
Cohesion: 0.25
Nodes (4): Bi(), Ci(), Fi(), ls

### Community 91 - "fa"
Cohesion: 0.22
Nodes (8): ea(), fa(), ga(), ha, pa(), sa(), ta(), ua()

### Community 92 - "de"
Cohesion: 0.31
Nodes (3): ce(), de, he()

### Community 93 - "parse"
Cohesion: 0.25
Nodes (3): go(), ii(), parse()

### Community 96 - ".getLabels"
Cohesion: 0.25
Nodes (3): buildTicks(), init(), po()

### Community 98 - "analyze_solar_anomaly_with_ai"
Cohesion: 0.43
Nodes (5): analyze_solar_anomaly_with_ai(), Invoca o Agente Especialista Fotovoltaico (Gemini AI) para analisar a anomalia s, patch, test_solar_ai_expert_no_key(), test_solar_ai_expert_with_gemini_key()

## Knowledge Gaps
- **154 isolated node(s):** `generate_daily.sh script`, `run_tests.sh script`, `PYTHONPATH`, `00_setup_python.sh script`, `01_setup_env.sh script` (+149 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ns()` connect `ns` to `.getLabels`, `.getDataset`, `._resolveElementOptions`, `beforeUpdate`, `☀️ 1. Resumo das Etapas Implementadas (Roadmap Solar)`, `send_daily_solar_telegram_report`, `va`, `bn`, `test_auth.py`, `chart.min.js`, `.getDataTimestamps`, `.getContext`, `test_web_config.py`, `parse`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `an()` connect `test_auth.py` to `script.js`, `send_daily_solar_telegram_report`, `inRange`, `va`, `da`, `chart.min.js`, `.bindResponsiveEvents`, `.getContext`, `test_web_config.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `no` connect `no` to `.getLabels`, `send_daily_solar_telegram_report`, `va`, `d`, `da`, `chart.min.js`, `.getDataTimestamps`, `En`, `test_web_config.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `s()` (e.g. with `chart.min.js` and `._updateHiddenIndices()`) actually correct?**
  _`s()` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `o()` (e.g. with `ai()` and `.buildOrUpdateScales()`) actually correct?**
  _`o()` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `generate_daily.sh script`, `run_tests.sh script`, `PYTHONPATH` to the rest of the system?**
  _154 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Diário de Alterações (Changelog) - 21/06/2026` be split into smaller, more focused modules?**
  _Cohesion score 0.041666666666666664 - nodes in this community are weakly interconnected._