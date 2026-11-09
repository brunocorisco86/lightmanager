# Roadmap — Confiabilidade da iluminação (pós-incidente 08/11/2026)

Backlog detalhado: [BACKLOG.md](BACKLOG.md) · Relatório: [RELATORIO_INCIDENTE_2026-11-08.md](RELATORIO_INCIDENTE_2026-11-08.md)

Princípio: **o servidor é a única autoridade; o Wemos só age sozinho se ficar realmente isolado, e nunca com relógio não confiável.**

## Fase 0 — Conter (1 dia)
B-01 (reflash do firmware atual), B-03 (corrigir dados de consumo), B-04 (validação).
Meta: zero flapping na próxima madrugada.

## Fase 1 — Observabilidade (até 7 dias)
B-02 (heartbeat com fw/uptime/hora), B-05 (detector de flapping + alerta Telegram), B-06 (log_analyzer conta desvios).
Meta: qualquer anomalia chega ao Telegram em < 10 min.

## Fase 2 — Robustez (até 14 dias)
B-07 (backoff no reforço), B-08 (sanity do relógio no firmware), B-09 (fallback nunca desliga com MQTT ok), B-10 (estabilizar offsets de nuvem), B-11 (reboot do Pi), B-12 (testes de regressão).
Meta: falha de um componente não derruba a iluminação.

## Fase 3 — Evolução (30 dias)
B-13 (OTA), B-14 (CI compila `.ino`), B-15 (dashboard de transições), B-16 (feedback de relé), B-17 (higiene do cron).

## KPIs
| KPI | Meta |
|-----|------|
| Transições de relé/noite (frente/fundos) | ≤ 4 |
| "Desvio detectado"/dia | ≤ 5 |
| Tempo para alertar anomalia | < 10 min |
| Firmware em produção = `main` | 100 % |
