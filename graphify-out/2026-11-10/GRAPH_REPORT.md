# Graph Report - 9_LIGHT_MANAGER  (2026-11-10)

## Corpus Check
- 100 files · ~73,122 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1488 nodes · 3136 edges · 125 communities (85 shown, 35 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 116 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c5190c5e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Diário de Alterações (Changelog) - 21/06/2026
- get_db_conn
- solar_worker.py
- script.js
- bot.py
- test_housekeeping.py
- ⚡ Comandos Úteis e Operação em Produção
- Light Manager
- P2
- What You Must Do When Invoked
- test_flapping_regression.py
- log_analyzer.py
- Light Manager Workspace Rules
- 📦 Configuração de Backup: Cloudflare R2
- an
- ⚡ Fluxo de Deploy em Produção
- Light Manager - Roadmap & Next Steps
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
- a
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
- ._generate
- va
- main.py
- DVRIPClient
- beforeUpdate
- eo
- inRange
- d
- test_web_api.py
- solar_scraper.py
- run_monthly_report_flow
- jn
- tn
- bn
- send_daily_solar_telegram_report
- zt
- o
- l
- updateElements
- b
- ns
- TestSolarWorkerPerformance
- getPixelForValue
- bo
- fix_flapping_data.py
- Diário de Alterações (Changelog) - 01/08/2026 (Roadmap Fotovoltaico Completo)
- .isHorizontal
- Skill: NVR XiongMai `NBD88X09S-KL` (`nvr_xiongmai`)
- graphify reference: extra exports and benchmark
- .getContext
- rs
- graphify reference: query, path, explain
- fa
- check_abrupt_power_drop_and_rain
- send_telegram_message
- Diário de Alterações (Changelog)
- no
- graphify reference: add a URL and watch a folder
- En
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- TestAutomationImprovements
- graphify reference: GitHub clone and cross-repo merge
- fetch_solar_forecast
- graphify reference: transcribe video and audio
- extraction-spec.md
- n
- 🎙️ 7. Implementações do Dia 11/07/2026 (Comandos de Voz via Gemini API e Reorganização de Documentos)
- ☀️ 1. Resumo das Etapas Implementadas (Roadmap Solar)
- 08_flash_firmware.sh
- DIARIO_ALTERACOES.md
- ._computeLabelItems
- draw
- ⚡ 5. Implementações do Dia 24/06/2026 (Time Sync Híbrido, Rollover e Tarifas ANEEL)
- 🧠 8. Implementações do Dia 12/07/2026 (Housekeeping, Resiliência de DNS Unbound e Rate-limiting no Telegram)
- test_auth.py
- 🛠️ 2. Melhorias e Correções Implementadas
- 💡 4. Implementações do Dia 23/06/2026 (Consumo e Resiliência)
- s
- test_web_config.py
- da
- test_command_reliability.py
- ko
- ho
- get_nvr_channels_summary
- .getDecimalForPixel

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
- `test_extract_errors_ignores_self_logs()` --calls--> `extract_errors()`  [EXTRACTED]
  tests/test_log_analyzer.py → scripts/log_analyzer.py
- `test_get_weather_and_solar_context()` --calls--> `get_weather_and_solar_context()`  [EXTRACTED]
  tests/test_log_analyzer.py → scripts/log_analyzer.py

## Import Cycles
- None detected.

## Communities (125 total, 35 thin omitted)

### Community 0 - "Diário de Alterações (Changelog) - 21/06/2026"
Cohesion: 0.17
Nodes (12): 🔍 1. Problemas Identificados (Erros em Produção), ⛅ 3. Implementações do Dia 22/06/2026 (Sincronização Meteorológica), ⚡ 6. Implementações do Dia 25/06/2026 (Persistência de Override Manual e Correção de Oscilação de Fallback), ☀️ 9. Implementações do Dia 04/08/2026 (Exibição de Geração e Saúde Solar no Comando `/status` do Bot Telegram), 🔄 Correção de Oscilação ao Ligar (Conflito de Fallback e Trigger Solar), 🔌 Dispositivo Wemos Sem Comunicação (MQTT Timeout), Diário de Alterações (Changelog) - 21/06/2026, 📅 Erros Críticos de Script Inexistente no Cron (+4 more)

### Community 1 - "get_db_conn"
Cohesion: 0.17
Nodes (23): delete, get, delete_point(), download_service_log(), ensure_light_points_schema(), get_consumption_history(), get_db_conn(), get_db_pool() (+15 more)

### Community 2 - "solar_worker.py"
Cohesion: 0.14
Nodes (24): Ciclo principal de coleta de telemetria solar: 1. Scraping via HTTP (POST…, run_solar_scraping_cycle(), append_nvr_log(), check_expired_camera_timers(), fetch_sun_data_with_retry(), get_db_conn(), get_db_pool(), get_today_sun_data() (+16 more)

### Community 3 - "script.js"
Cohesion: 0.12
Nodes (23): appendLogLine(), createNewPoint(), deletePoint(), fetchData(), formatHistorySource(), formatRuleBadge(), loadCharts(), loadConfigList() (+15 more)

### Community 4 - "bot.py"
Cohesion: 0.24
Nodes (19): check_auth(), cmd_desliga(), cmd_liga(), cmd_relatorio(), cmd_solar(), cmd_start(), cmd_status(), execute_light_command() (+11 more)

### Community 5 - "test_housekeeping.py"
Cohesion: 0.24
Nodes (12): check_mosquitto_health(), get_db_connection(), main(), prune_database(), prune_logs(), Tenta conectar ao PostgreSQL usando variáveis de ambiente do .env., Preserva integralmente todos os registros de tabelas no banco de dados…, Roda logrotate e deleta arquivos de log rotacionados/comprimidos mais antigos… (+4 more)

### Community 6 - "⚡ Comandos Úteis e Operação em Produção"
Cohesion: 0.17
Nodes (11): 1. Status Geral dos Serviços, 2. Reiniciar Serviços (Scripts de Autocura), 3. Visualizar Logs em Tempo Real, 4. Recarregar o Agendador Crontab, 5. Gestão de Usuários Administrativos, 🧪 Ambiente de Desenvolvimento & Testes Locais, 🌐 Ambiente de Produção (`ssh alpine`), 🛠️ Arquitetura do Sistema (+3 more)

### Community 7 - "Light Manager"
Cohesion: 0.18
Nodes (10): 🛠️ Arquitetura, 🧪 Como Rodar a Suíte de Testes Localmente, 🚀 Funcionalidades, ⚙️ Funcionalidades de Resiliência de Automação, ⚙️ Gestão e Manutenção, Light Manager, 🛡️ Mecanismos de Confiabilidade & Testes Locais, 🚀 Operação em Produção (Alpine Linux) (+2 more)

### Community 8 - "P2"
Cohesion: 0.06
Nodes (30): B-01 — Recompilar e gravar o firmware atual no Wemos (S/M) 🔴, B-02 — Heartbeat do Wemos com `fw`, `uptime_s`, `local_time`, `clock_synced` (M), B-03 — Corrigir dados de consumo das noites 07 e 08/11 (M), B-04 — Checklist de validação pós-flash (S), B-05 — Detector de flapping + alerta (M), B-06 — `log_analyzer.py` contar "Desvio detectado" (S), B-07 — Backoff no reforço de estado (M), B-08 — Sanity do relógio no firmware (M) (+22 more)

### Community 9 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 10 - "test_flapping_regression.py"
Cohesion: 0.12
Nodes (24): check_and_record_transition(), last_seen_file_for(), on_message(), Retorna o arquivo de last_seen do embarcado dono do tópico (muro/aux ->…, Atualiza o timestamp local de última atividade de um embarcado (wemos ou esp32)., Registra transições e detecta oscilações anômalas (flapping) em tópicos…, touch_last_seen(), Um carro ou moto veloz dispara apenas 1 pulso rápido (< 2s) -> relé NÃO liga. (+16 more)

### Community 11 - "log_analyzer.py"
Cohesion: 0.22
Nodes (14): clean_timestamp(), extract_errors(), get_ai_summary(), get_weather_and_solar_context(), main(), Busca o contexto de meteorologia e geração solar diária para informar o agente…, Envia os erros para a API do Gemini e obtém o resumo., Envia uma mensagem de texto pelo bot do Telegram com tratamento de Rate-… (+6 more)

### Community 12 - "Light Manager Workspace Rules"
Cohesion: 0.22
Nodes (8): 🌐 Ambiente de Produção, 🕒 Fuso Horário e Registro, ⚡ Gestão de Consumo e Tarifas, 🛡️ Guardrails & Resiliência, Light Manager Workspace Rules, 🔌 Lógica de Hardware (ESP8266 Wemos D1 R1), ⚙️ Manutenção de Serviços, 🧪 Testes de Integridade

### Community 13 - "📦 Configuração de Backup: Cloudflare R2"
Cohesion: 0.22
Nodes (8): 1. Configuração no Painel Cloudflare, 2.1 Atualizar o `.env`, 2.2 Dependências, 2. Configuração no Servidor (Local), 3. Execução e Teste, 4. Agendamento (Crontab), 5. Política de Retenção e Custos (Free Tier), 📦 Configuração de Backup: Cloudflare R2

### Community 14 - "an"
Cohesion: 0.05
Nodes (25): addBox(), afterDatasetsUpdate(), an(), ca(), ct(), fs(), ge(), generateLabels() (+17 more)

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
Cohesion: 0.22
Nodes (8): Valida se as bibliotecas críticas do bot estão instaladas., Verifica se as variáveis mínimas do bot existem no .env, Verifica se o arquivo bot.py não tem erros de sintaxe e pode ser carregado., Valida a execução sem exceções de NameError/TypeError da função…, test_bot_dependencies(), test_bot_env_vars(), test_bot_syntax(), test_get_solar_status_summary()

### Community 20 - "chart.min.js"
Cohesion: 0.05
Nodes (17): be(), cn(), destroy(), es(), fe(), Gt(), hn(), Jo() (+9 more)

### Community 21 - "⚡ Fluxo de Trabalho do Agente"
Cohesion: 0.33
Nodes (5): 1. Verificação Prévia de Hardware, 2. Executar o Script Unificado de Flash, 3. Dicas de Bootloader no ESP32-C3 Supermini, ⚡ Fluxo de Trabalho do Agente, Skill: Gravador de Firmware Embarcado (embedded_flasher)

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

### Community 27 - "a"
Cohesion: 0.16
Nodes (7): a(), Di(), is(), pi(), r(), we(), zi()

### Community 28 - "05_register_lights.py"
Cohesion: 0.83
Nodes (3): get_db_connection(), init_db(), register_point()

### Community 29 - "manage_users.py"
Cohesion: 0.83
Nodes (3): create_user(), get_db_connection(), init_users_table()

### Community 58 - "._generate"
Cohesion: 0.21
Nodes (6): buildLookupTable(), _generate(), _getTimestampsForTable(), initOffsets(), nt(), zo()

### Community 59 - "va"
Cohesion: 0.19
Nodes (5): afterEvent(), f(), ss(), update(), va

### Community 60 - "main.py"
Cohesion: 0.23
Nodes (13): BaseModel, post, put, check_password(), CommandRequest, create_point(), login(), LoginRequest (+5 more)

### Community 61 - "DVRIPClient"
Cohesion: 0.09
Nodes (27): build_decoder_entry(), discover_xiongmai_udp(), ensure_night_led_disabled(), evaluate_and_heal(), expected_nvr_mac(), fetch_lansentry_mac_map(), hex_ip_to_str(), main() (+19 more)

### Community 63 - "eo"
Cohesion: 0.08
Nodes (13): afterDraw(), afterUpdate(), Do(), eo(), gs(), ki(), oa(), Oe() (+5 more)

### Community 64 - "inRange"
Cohesion: 0.12
Nodes (21): ao(), average(), dataset(), getCenterPoint(), Hs, _i(), index(), inRange() (+13 more)

### Community 65 - "d"
Cohesion: 0.12
Nodes (4): buildTicks(), d(), determineDataLimits(), po()

### Community 66 - "test_web_api.py"
Cohesion: 0.30
Nodes (11): patch, test_get_consumption_history_success(), test_get_history_success(), test_get_solar_generation_curve_success(), test_get_status_db_error(), test_get_status_success(), test_get_sun_times_cached(), test_get_sun_times_failure() (+3 more)

### Community 67 - "solar_scraper.py"
Cohesion: 0.08
Nodes (43): analyze_solar_anomaly_with_ai(), Invoca o Agente Especialista Fotovoltaico (Gemini AI) para analisar a anomalia…, cache_working_ip(), check_solar_anomalies(), fetch_solar_telemetry(), find_ip_in_arp(), get_inverter_ip_hint(), get_inverter_mac() (+35 more)

### Community 68 - "run_monthly_report_flow"
Cohesion: 0.15
Nodes (21): fetch_monthly_solar_data(), generate_ai_monthly_consultant_report(), get_db_conn(), get_target_month_range(), get_tariff_rate(), Obtém a tarifa da concessionária (R$/kWh) gravada no DB ou parâmetro local., Gera o gráfico de barras mensal da geração diária (kWh) usando Matplotlib…, Comprime o contexto e invoca o Agente Consultor IA (Gemini API) para emitir… (+13 more)

### Community 70 - "tn"
Cohesion: 0.07
Nodes (6): addElements(), Cs, nn(), os(), sn, tn

### Community 71 - "bn"
Cohesion: 0.17
Nodes (3): bn, dn(), pn()

### Community 72 - "send_daily_solar_telegram_report"
Cohesion: 0.24
Nodes (13): calculate_daily_summary(), fetch_daily_solar_data(), generate_solar_chart_png(), get_db_conn(), Gera o gráfico da curva sino de potência solar fotovoltaica usando Matplotlib…, Gera e envia o relatório diário de produção solar fotovoltaica para o Telegram., Busca todas as entradas de telemetria solar registradas no banco para o dia…, Calcula os indicadores resumidos (KPIs) da geração do dia. (+5 more)

### Community 73 - "zt"
Cohesion: 0.08
Nodes (12): bt, color(), Ft(), It(), kt(), mt(), qt(), _t() (+4 more)

### Community 74 - "o"
Cohesion: 0.15
Nodes (16): e(), ei(), gi(), je(), la(), mi(), o(), on() (+8 more)

### Community 75 - "l"
Cohesion: 0.15
Nodes (13): aa(), Fn(), Gn(), go(), ii(), l(), parse(), parseArrayData() (+5 more)

### Community 76 - "updateElements"
Cohesion: 0.19
Nodes (6): _calculateBarValuePixels(), getBasePixel(), getLabelAndValue(), getLabelForValue(), resolveDataElementOptions(), updateElements()

### Community 77 - "b"
Cohesion: 0.19
Nodes (5): b(), ce(), de, dt(), he()

### Community 78 - "ns"
Cohesion: 0.10
Nodes (3): As(), ns(), updateRangeFromParsed()

### Community 80 - "getPixelForValue"
Cohesion: 0.12
Nodes (10): Ae(), _calculateBarIndexPixels(), getPixelForValue(), _getRuler(), _getStackCount(), _getStackIndex(), _getStacks(), In() (+2 more)

### Community 84 - "Diário de Alterações (Changelog) - 01/08/2026 (Roadmap Fotovoltaico Completo)"
Cohesion: 0.40
Nodes (5): ⚡ 02/08/2026 - Correção de Oscilação de Luzes (Fuso Horário de Fallback MQTT BRT), 🧪 2. Validação & Deploy em Produção, 🛠️ Correções e Ajustes, 🐛 Diagnóstico do Problema (Luzes Piscando a Cada Minuto), Diário de Alterações (Changelog) - 01/08/2026 (Roadmap Fotovoltaico Completo)

### Community 85 - ".isHorizontal"
Cohesion: 0.18
Nodes (4): configure(), H(), mo(), xo

### Community 86 - "Skill: NVR XiongMai `NBD88X09S-KL` (`nvr_xiongmai`)"
Cohesion: 0.10
Nodes (19): 📹 1. Catálogo Mestre das 6 Câmeras (`D01` a `D06`), 2.1 Dois Pontos de Acesso Wi-Fi na LAN (`192.168.1.0/24`), 2.2 Arquitetura Dual-IP nas Câmeras XiongMai (`D01`, `D04` e `D06`), 2.3 Peculiaridades de `D02` (`IPC_XM210` V5.08) e `D05` (`Trolink ONVIF`), 🌐 2. Topologia de Rede e Comportamento por Modelo/SoC, 🔒 3. Erros Mapeados e Solução de Problemas, 🛡️ 4. Monitoramento de Saúde e Self-Healing com LanSentry (`scripts/camera_watchdog.py`), Automação via Cron (Ambiente de Produção Alpine) (+11 more)

### Community 87 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 88 - ".getContext"
Cohesion: 0.16
Nodes (4): Bi(), Ci(), Fi(), rt()

### Community 90 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 91 - "fa"
Cohesion: 0.16
Nodes (9): ea(), fa(), ga(), ha, ia(), pa(), sa(), ta() (+1 more)

### Community 92 - "check_abrupt_power_drop_and_rain"
Cohesion: 0.32
Nodes (11): check_abrupt_power_drop_and_rain(), Mantém histórico de potência solar dos últimos 20 minutos em disco., Detecta queda abrupta ou progressiva de geração solar no horário diurno (janela…, update_and_get_power_history(), patch, test_rain_alert_drop_below_100w(), test_rain_alert_gradual_window_drop(), test_rain_alert_morning_extended_hours() (+3 more)

### Community 93 - "send_telegram_message"
Cohesion: 0.26
Nodes (10): Envia uma notificação para o Telegram com tratamento de Rate-Limiting e…, send_telegram_message(), test_real_notification(), patch, Valida se a função de envio chama a URL correta do Telegram com o payload…, Valida se a função trata erros de rede ou status sem quebrar o worker., Garante que nada é enviado se o token não estiver configurado., test_send_telegram_message_failure() (+2 more)

### Community 94 - "Diário de Alterações (Changelog)"
Cohesion: 0.20
Nodes (10): 🛡️ 08/11/2026 - Confiabilidade da Iluminação & Mitigações Pós-Incidente (Flapping Noturno), ⚡ 09/11/2026 - Suporte a 4 Canais no Firmware Wemos D1 (Canais /muro e /aux), ⚡ 10/11/2026 - Arquitetura Dual-Firmware (Wemos D1 R1 + ESP32-C3 Supermini) e Gravador Unificado, 🚀 Demanda, 🚀 Demanda, 🐛 Diagnóstico do Incidente (Madrugada de 07 e 08/11/2026), Diário de Alterações (Changelog), 🛠️ Implementações e Mitigações Executadas (+2 more)

### Community 95 - "no"
Cohesion: 0.16
Nodes (4): beforeLayout(), getDecimalForValue(), no, qo()

### Community 96 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 97 - "En"
Cohesion: 0.17
Nodes (3): En, Fo(), init()

### Community 98 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 99 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 100 - "TestAutomationImprovements"
Cohesion: 0.27
Nodes (5): patch, Valida se o manual_override é limpo no banco ao bater o minuto do gatilho solar., Valida se os horários de fallback enviados ao Wemos se ajustam aos offsets…, Verifica se o manual_override ativa o estado desejado forçado independentemente…, TestAutomationImprovements

### Community 102 - "fetch_solar_forecast"
Cohesion: 0.29
Nodes (8): calculate_system_efficiency_factor(), fetch_solar_forecast(), get_db_conn(), Consulta a API Open-Meteo Solar Forecast e retorna a previsão estimada de…, Calcula o fator dinâmico de conversão (kWh por MJ/m²) baseado no histórico…, patch, test_calculate_system_efficiency_factor_default(), test_fetch_solar_forecast_success()

### Community 105 - "n"
Cohesion: 0.24
Nodes (3): n(), ne(), numeric()

### Community 106 - "🎙️ 7. Implementações do Dia 11/07/2026 (Comandos de Voz via Gemini API e Reorganização de Documentos)"
Cohesion: 0.67
Nodes (3): 🎙️ 7. Implementações do Dia 11/07/2026 (Comandos de Voz via Gemini API e Reorganização de Documentos), 🗣️ Reconhecimento de Comandos de Voz via Telegram Bot, 📂 Reorganização e Limpeza de Documentos (Eliminação de Redundâncias)

### Community 107 - "☀️ 1. Resumo das Etapas Implementadas (Roadmap Solar)"
Cohesion: 0.25
Nodes (8): ☀️ 1. Resumo das Etapas Implementadas (Roadmap Solar), 📈 Etapa 1: Relatório Pós-Pôr do Sol com Gráfico Matplotlib Headless, 🔮 Etapa 2: Previsão Solar via Open-Meteo & Calibração Dinâmica, 📊 Etapa 3: Curva Sino de Potência no Dashboard Frontend Web, 🚨 Etapa 4: Alertas de Anomalia + Agente IA Especialista em Elétrica Solar (Gemini API), 🌧️ Etapa 5: Alerta Preventivo de Chuva (Drop Solar + Open-Meteo), 📊 Etapa 6: Relatório Mensal Consolidado + Agente Consultor IA (Cron Dia 01 às 06:30h), 🚀 Resiliência de Scraping por Endereço MAC (Inversor Solar)

### Community 109 - "DIARIO_ALTERACOES.md"
Cohesion: 0.29
Nodes (6): 🔍 1. Problemas e Solicitações, 🛠️ 2. Resumo de Execução em Produção, 🛡️ Definição de Guardrails do Agente, Diário de Alterações (Changelog) - 19/07/2026, 💾 Mosquitto persistence & Desgaste de Cartão SD (Overhead de I/O), 🧹 Prunagem de Banco de Dados e Logs (Housekeeping)

### Community 110 - "._computeLabelItems"
Cohesion: 0.16
Nodes (3): getPixelForTick(), qs(), Xs()

### Community 111 - "draw"
Cohesion: 0.11
Nodes (18): ai(), at(), beforeDraw(), draw(), Ee(), getMaxOverflow(), getRange(), hi() (+10 more)

### Community 112 - "⚡ 5. Implementações do Dia 24/06/2026 (Time Sync Híbrido, Rollover e Tarifas ANEEL)"
Cohesion: 0.40
Nodes (5): ⚡ 5. Implementações do Dia 24/06/2026 (Time Sync Híbrido, Rollover e Tarifas ANEEL), ⚡ Correção de Duração Truncada por Reforço Horário, 💰 Integração Tarifária e Financeira (ANEEL & Impostos), 🌙 Mecanismo de Virada de Dia (Rollover), ⏰ Sincronização de Tempo Híbrida (Remoção do NTP no Embarcado)

### Community 113 - "🧠 8. Implementações do Dia 12/07/2026 (Housekeeping, Resiliência de DNS Unbound e Rate-limiting no Telegram)"
Cohesion: 0.40
Nodes (5): 🧠 8. Implementações do Dia 12/07/2026 (Housekeeping, Resiliência de DNS Unbound e Rate-limiting no Telegram), 🤖 Análise e Notificação Inteligente de Erros (Gemini 2.5 Flash + Telegram), ☀️ Coleta e Scraping de Dados de Geração Solar (Inversor LAN 192.168.1.13), 🧹 Housekeeping de Logs (logrotate e copytruncate), 🌐 Watchdog Híbrido de Internet e DNS Local Unbound (Governança e Autorrecuperação)

### Community 114 - "test_auth.py"
Cohesion: 0.22
Nodes (9): get_db_connection(), fixture, Valida login com credenciais corretas, Valida falha com senha incorreta, Valida falha com usuário inexistente, setup_test_user(), test_login_success(), test_login_user_not_found() (+1 more)

### Community 115 - "🛠️ 2. Melhorias e Correções Implementadas"
Cohesion: 0.50
Nodes (4): 1. Refatoração do Watchdog do Bot do Telegram, 2. Criação do Watchdog Local de Firmware (Resiliência do Wemos), 🛠️ 2. Melhorias e Correções Implementadas, 3. Desenvolvimento do Relatório Diário de Consumo via Telegram

### Community 116 - "💡 4. Implementações do Dia 23/06/2026 (Consumo e Resiliência)"
Cohesion: 0.50
Nodes (4): 💡 4. Implementações do Dia 23/06/2026 (Consumo e Resiliência), 🔌 Correção do Desligamento Precoce da Luz (Bug de Limite NTP), 🛡️ Fallback Local de Cronograma no Firmware (Wemos Offline), 📊 Registro de Duração e Consumo de Energia em kWh

### Community 117 - "s"
Cohesion: 0.31
Nodes (7): g(), s(), label(), m(), g(), p(), to()

### Community 118 - "test_web_config.py"
Cohesion: 0.36
Nodes (5): get_db_connection(), fixture, setup_db(), test_nvr_detections_endpoint(), test_solar_history_endpoint()

### Community 119 - "da"
Cohesion: 0.32
Nodes (6): beforeDatasetDraw(), beforeDatasetsDraw(), da(), Ie(), na(), ze()

### Community 120 - "test_command_reliability.py"
Cohesion: 0.29
Nodes (6): Valida se o comando é enviado com sucesso via API e se o MQTT está conectado.…, Valida rejeição de payloads malformados, Valida se a API aguenta múltiplos comandos rápidos sem travar o loop MQTT, test_command_invalid_payload(), test_command_mqtt_qos_delivery(), test_rapid_commands()

### Community 121 - "ko"
Cohesion: 0.29
Nodes (4): j(), ko, vo(), wo()

### Community 122 - "ho"
Cohesion: 0.40
Nodes (5): ho(), inXRange(), inYRange(), oo(), Y()

### Community 123 - "get_nvr_channels_summary"
Cohesion: 0.50
Nodes (4): get_nvr_channels_summary(), Retorna lista estruturada dos 9 canais do NVR (somente-leitura)., get_nvr_channels(), Retorna os 9 canais do NVR XiongMai (com cache de 60s e fallback caso NVR…

## Knowledge Gaps
- **200 isolated node(s):** `generate_daily.sh script`, `run_tests.sh script`, `PYTHONPATH`, `00_setup_python.sh script`, `01_setup_env.sh script` (+195 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 454 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ns()` connect `ns` to `d`, `tn`, `l`, `updateElements`, `an`, `getPixelForValue`, `chart.min.js`, `.getContext`, `va`, `beforeUpdate`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `fetch_solar_forecast()` connect `fetch_solar_forecast` to `get_db_conn`, `solar_scraper.py`, `send_daily_solar_telegram_report`, `log_analyzer.py`, `main.py`, `check_abrupt_power_drop_and_rain`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `an()` connect `an` to `inRange`, `tn`, `b`, `chart.min.js`, `s`, `.getContext`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `s()` (e.g. with `beforeUpdate()` and `da()`) actually correct?**
  _`s()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `o()` (e.g. with `ai()` and `da()`) actually correct?**
  _`o()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `a()` (e.g. with `ai()` and `cn()`) actually correct?**
  _`a()` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `generate_daily.sh script`, `run_tests.sh script`, `PYTHONPATH` to the rest of the system?**
  _200 weakly-connected nodes found - possible documentation gaps or missing edges._