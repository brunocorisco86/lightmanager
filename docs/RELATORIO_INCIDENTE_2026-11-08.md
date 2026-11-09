# Relatório de Incidente — Luzes ligando/desligando na madrugada de 08/11/2026

> Análise feita em 08/11/2026 ~21h (BRT) lendo logs em produção (`ssh alpine`, Raspberry Pi 3B, `/home/bruno/lightmanager/logs`) e o código/firmware do repositório. **Nenhuma alteração foi feita em produção.**

## 1. Resumo executivo

Entre **02:55 e 05:55 (BRT)** as lâmpadas **frente** e **fundos** ficaram em ciclo de ~60 s:
`Wemos desliga (OFF) → ~17–60 s depois o Solar Worker "reforça" ON → 1 min depois o Wemos desliga de novo`.
Foram **~175 ciclos** (188 OFFs registrados no dia). O mesmo ocorreu em **07/11 entre 02:39 e ~05:39** (~320 desvios).

**Causa raiz (alta confiança):** o ESP8266 (Wemos) decide sozinho, a cada 60 s, que "já é dia" e abre os relés, porque o relógio dele está **3 h adiantado (comporta-se como UTC)** e o `fallback/off` enviado pelo servidor é um horário BRT.
O firmware **em execução** parece ser um binário antigo (jun/2026) que não tem as correções do commit `ea4e913` (TZ BRT3 + exigir 2 min offline antes do fallback).

## 2. Evidências

| # | Evidência | Fonte |
|---|-----------|-------|
| 1 | Primeiro OFF em `02:55:19`; `fallback/off` publicado = `05:55`. 02:55 + 3 h = 05:55. | `solar.log` (00:00:29: `ON=18:43, OFF=05:55`) |
| 2 | Em 07/11 o `fallback/off` era `05:38/05:55` e os desvios começaram em `02:39`. 02:39 + 3 h = 05:39 (OFF 05:38 + 1). Mesma regra. | `solar.log.1` |
| 3 | O flapping termina em `05:54/05:55` BRT: a partir daí o servidor também deseja OFF (nascer do sol 05:44 + offset), então o "conflito" some. | `solar.log`, `sun_cache.json` (sunrise 08:44 UTC) |
| 4 | O OFF aparece em `home/outdoor/*/state` **sem nenhum `/set` OFF** do servidor antes → quem publicou foi o próprio Wemos, no tick de 60 s (mesmo segundo do heartbeat, `:19.7`). | `solar.log`, `bot.log` |
| 5 | O `.ino` atual **não publica estado** no bloco de fallback e só age com MQTT offline ≥ 2 min. O comportamento observado (publica OFF com MQTT conectado) só é compatível com o código **antigo**, anterior ao `ea4e913` (26/07). | `git show ea4e913` |
| 6 | O `wemos_light.bin` versionado foi compilado em 25/06 (último commit do `.bin` antes do fix de TZ). Nunca foi recompilado/regravado depois do fix. | `git log -- firmware/wemos_light/wemos_light.bin` |
| 7 | O servidor está saudável: heartbeats a cada 60 s, RSSI −50 dBm, MQTT estável. Erros do bot Telegram (timeouts) são rede externa e **não relacionados**. | `solar.log`, `bot.log` |
| 8 | Evento paralelo: Pi reiniciou ~04:18 (uptime 17 h às 21:20; bot recebeu SIGTERM 04:17). O flapping continuou depois → não é causa, mas é um segundo ponto a investigar. | `uptime`, `bot.log` |

### Por que só começou em 07/11 (e não nos dias 03–06)?
**Não confirmado.** Nos dias 03–06 não há desvios de madrugada. Hipóteses: (a) o Wemos reiniciou ~06–07/11 e passou a sincronizar relógio/fallback de forma diferente; (b) a mudança de offsets de nuvem (`weather_offset_sync.py`) alterou o `fallback/off`. Para fechar, é preciso ler a serial do Wemos ou adicionar `uptime`/`fw_version` ao heartbeat (ver backlog B-01/B-02).

## 3. Impactos

- Lâmpadas apagando ~60 s a cada ciclo durante 3 h (segurança/câmeras com menos luz).
- Desgaste dos relés (~350 comutações/noite) e do SD Card (cada transição grava no PostgreSQL).
- **Dados de consumo distorcidos:** dezenas de registros `mqtt_capture` com 39–60 s de duração em 07 e 08/11.
- Ruído nos logs (`Desvio detectado` ×~660 em 2 noites) mascarando problemas reais.
- Sem nenhum alerta automático ao usuário.

## 4. Lacunas de projeto reveladas

1. **Duas fontes de decisão** (Wemos × Solar Worker) disputando o relé sem arbitragem.
2. Solar Worker "reforça" indefinidamente, sem backoff nem detecção de flapping.
3. Firmware compilado ≠ firmware em produção ≠ `.ino` no repositório; sem versão visível.
4. Heartbeat não informa hora local do Wemos, uptime nem versão → impossível detectar skew de relógio remotamente.
5. Fallback de horário usa `fallback/off` do servidor como se fosse "verdade", sem sanity check.
6. Sem alerta de anomalia (N transições em X min).

## 5. Ação imediata sugerida (curta)

1. Compilar e gravar o `wemos_light.ino` atual (skill `embedded_flasher`, `scripts/08_flash_wemos.sh`) — resolve a causa raiz.
2. Validar com `mosquitto_sub -t 'home/outdoor/#' -v` que não há OFF espúrio no tick de 60 s.
3. Seguir [BACKLOG.md](BACKLOG.md) (itens P0 primeiro) e [ROADMAP_CONFIABILIDADE.md](ROADMAP_CONFIABILIDADE.md).
