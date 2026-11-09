# Backlog executável — Light Manager

Escrito para ser executado por um modelo mais simples, **na ordem**. Cada item tem arquivos, passos e critério de aceite.
Regras do projeto (ver `.agents/AGENTS.md`): fuso BRT; `./run_tests.sh` antes de deploy; deploy via git (`git push` local → `git pull` em `ssh alpine`, dir `/home/bruno/lightmanager`); após alterar serviço rodar `bash scripts/restart_<servico>.sh`; **todo deploy termina com notificação de teste no Telegram**; rodar `graphify update .` após mudar código. Relé é Active Low. Fallback MQTT é sempre `HH:MM` em BRT.

Contexto: ver [RELATORIO_INCIDENTE_2026-11-08.md](RELATORIO_INCIDENTE_2026-11-08.md).

Legenda: P0 = fazer já · P1 = semana · P2 = depois · Esforço: S ≤1h, M ≤½ dia, L ≥1 dia

---

## P0

### B-01 — Recompilar e gravar o firmware atual no Wemos (S/M) 🔴
**Por quê:** firmware em produção é antigo (causa raiz do flapping).
**Passos:**
1. Ler a skill `embedded_flasher` (`.agents/skills/embedded_flasher/SKILL.md`) e `scripts/08_flash_wemos.sh`.
2. Compilar `firmware/wemos_light/wemos_light.ino` (arduino-cli, placa `esp8266:esp8266:d1`) gerando novo `wemos_light.bin`.
3. Conferir: `strings firmware/wemos_light/wemos_light.bin | grep BRT` deve existir e `git log` deve mostrar o novo `.bin`.
4. Gravar no Wemos (192.168.1.111) via esptool/OTA conforme a skill. Fazer em horário de dia (lâmpadas OFF).
5. Commit `build(firmware): recompila wemos_light.bin com fixes de TZ e fallback`.
**Aceite:** na madrugada seguinte, `grep -a "Desvio detectado" logs/solar.log` retorna ≤ 5 linhas; heartbeat continua a cada 60 s.

### B-03 — Corrigir dados de consumo das noites 07 e 08/11 (M)
**Por quê:** `mqtt_capture` curtos poluem relatórios.
**Passos:**
1. Em produção, consultar o PostgreSQL: eventos/consumo dos pontos `home/outdoor/frente` e `fundos` entre `2026-11-07 02:39` e `05:55` e `2026-11-08 02:55` e `05:55` (BRT, `TIMESTAMPTZ`). Descobrir nomes das tabelas em `scripts/05_register_lights.py`.
2. **Fazer backup antes** (`pg_dump` das tabelas afetadas).
3. Criar `scripts/fix_flapping_data.py` (idempotente, com `--dry-run` default): colapsa a sequência ON/OFF do intervalo em um único período ON contínuo e recalcula kWh (potência × duração, mesma fórmula do `solar_worker.py` linha ~184).
4. Rodar com `--dry-run`, mostrar resultado ao usuário, só então `--apply`.
**Aceite:** relatório diário (`reports/generate_daily.sh`) das duas noites mostra consumo contínuo coerente (~3 h a mais ligadas).

### B-04 — Checklist de validação pós-flash (S)
1. `ssh alpine`; `mosquitto_sub -h localhost -u <user> -P <pass> -t 'home/outdoor/#' -v` por 10 min à noite: sem `state OFF` sem `set OFF` prévio.
2. `grep -a -c "Desvio" logs/solar.log` do dia seguinte.
3. Disparar notificação de teste Telegram (`scripts/test_telegram_real.py`).
**Aceite:** os três itens ok, registrados em `DIARIO_ALTERACOES.md`.

---

## P1

### B-02 — Heartbeat do Wemos com `fw`, `uptime_s`, `local_time`, `clock_synced` (M)
**Arquivos:** `firmware/wemos_light/wemos_light.ino` (bloco heartbeat no fim do `loop()`), `scripts/solar_worker.py` (handler do heartbeat, procurar "Heartbeat recebido").
**Passos:**
1. Adicionar `#define FW_VERSION "2026.11.1"`.
2. Acrescentar ao JSON: `"fw"`, `"uptime_s": millis()/1000`, `"hhmm": "HH:MM"` (de `localtime`), `"synced": time(nullptr)>1700000000`.
3. No solar_worker, logar esses campos e comparar `hhmm` com `datetime.now(BR_TZ)`; se diferença > 2 min → `logging.warning("⏱️ Skew de relógio do Wemos ...")` e Telegram (1×/hora).
4. Recompilar/gravar (B-01 de novo) e atualizar teste em `tests/`.
**Aceite:** log mostra skew ≈ 0; teste unitário do parse do heartbeat passa.

### B-05 — Detector de flapping + alerta (M)
**Arquivo:** `scripts/solar_worker.py` (onde ocorre "Transição de estado").
**Passos:**
1. Manter `deque` de timestamps de transições por tópico.
2. Se ≥ 6 transições em 10 min (excluindo `muro`, que é gatilho de câmera) → `send_telegram_message("⚠️ Flapping em <topic>…")` e `send_ntfy_message`; limitar a 1 alerta/hora por tópico.
3. Teste em `tests/` simulando 6 transições.
**Aceite:** teste passa; alerta chega no Telegram em simulação.

### B-06 — `log_analyzer.py` contar "Desvio detectado" (S)
Em `scripts/log_analyzer.py` (roda às 19h) incluir contagem de `Desvio detectado` do dia; se > 10, entrar no resumo crítico.
**Aceite:** com log sintético com 20 linhas, o resumo as menciona.

---

## P2

### B-07 — Backoff no reforço de estado (M)
`scripts/solar_worker.py` ~linha 545 (`# 2. Reforço de Estado`). Se o mesmo `(topic, desired_state)` já foi reforçado ≥ 3× nos últimos 10 min, passar a reforçar no máximo a cada 5 min e logar uma vez "backoff ativo". Resetar quando o estado bater com o desejado por ≥ 5 min.
**Aceite:** teste unitário: 10 desvios seguidos geram ≤ 4 publicações em 10 min simulados.

### B-08 — Sanity do relógio no firmware (M)
`wemos_light.ino`: guardar `last_time_sync_ms` ao receber `home/outdoor/time`. Funções de fallback só valem se `millis() - last_time_sync_ms < 15*60*1000`. Sem sincronização recente → não decide por horário.
**Aceite:** simulação: sem mensagem de tempo por 20 min, nenhum relé muda por conta própria.

### B-09 — Fallback local nunca desliga com MQTT conectado (S)
Revisar `loop()`: os dois blocos de fallback já exigem `is_mqtt_offline_sustained`; adicionar comentário/`static_assert`-like guard e teste de lógica (`isFallbackNightTime`) em um sketch host (`tests/firmware_logic_test.cpp`, compila com g++).
**Aceite:** teste host cobre virada de meia-noite e `on_total > off_total`.

### B-10 — Estabilizar offsets de nuvem (M)
`scripts/weather_offset_sync.py` roda às 02:00 e 17:00 e muda o `fallback` (ex.: 05:38 ↔ 05:55, ON 18:42 ↔ 18:59), causando também um desvio ON→OFF às 18:43 em 07/11.
Passos: (1) limitar variação a ±10 min em relação ao valor base; (2) não alterar offsets dentro de 30 min do nascer/pôr do sol; (3) logar valores antes/depois.
**Aceite:** teste com cobertura de nuvens simulada nunca produz horário fora do intervalo.

### B-11 — Investigar reboot do Pi às ~04:18 de 08/11 (M)
Em `ssh alpine`: `dmesg | tail -100`, `last -x | head`, `logs/boot.log`, `df -h`, `free -m` (só ~25 MB livres de 906 MB), tensão (`vcgencmd get_throttled` se disponível), SD card. Registrar conclusão em `docs/`.
**Aceite:** causa identificada ou descartada; se for memória, avaliar swap/zram.

### B-12 — Testes de regressão do incidente (M)
Criar `tests/test_flapping_regression.py` reproduzindo: estado desejado ON, Wemos reporta OFF repetidamente → verifica backoff (B-07) e alerta (B-05). Rodar `./run_tests.sh`.

---

## Futuro

- **B-13 OTA** do firmware (ArduinoOTA) para evitar cabo e deixar a versão rastreável (L).
- **B-14 CI**: GitHub Action compilando o `.ino` com `arduino-cli`; falhar se `.ino` mudou e `.bin` não (L).
- **B-15 Dashboard** de transições/dia na web (`web/`, `web_api/main.py`) com KPI do roadmap (M).
- **B-16 Feedback de relé** (sensor de corrente/optoacoplador) para confirmar estado real (L, depende de hardware).
- **B-17 Hardening de cron:** verificar duplicidade de entradas no `crontab -l` de produção vs `crontab_template.txt` (S).
