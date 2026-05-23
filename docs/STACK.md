# Stack do Sistema - Light Manager

## Arquitetura e Hardware
- **Cérebro:** Raspberry Pi 3B.
- **SO Principal:** Alpine Linux (escolhido por seu minimalismo, focado em rodar na RAM).
- **Atuadores:** Wemos D1 R1 (ESP8266) com Relé de 2 canais (Active Low).

## Software e Comunicação
- **Broker MQTT:** Eclipse Mosquitto 2.0+ (Instalação nativa via `apk`).
- **Protocolo IoT:** MQTT com autenticação por senha e persistência local `/var/lib/mosquitto/`.
- **DNS/Rede:** DNS local via Unbound (opcional) e IP Estático configurado no firmware.

## Persistência de Dados
- **Banco de Dados:** PostgreSQL 15+ (Rodando via Docker).
- **Tipagem Temporal:** Uso de `TIMESTAMPTZ` para garantir integridade de fuso horário (GMT-3).
- **Esquema:** Tabelas `light_points` e `light_events` com metadados de fonte (`source`).

## Lógica e Automação (Python 3.11+)
Ambiente virtualizado (`.venv`) contendo:
1. **Solar Worker & Event Logger:** Gerencia gatilhos solares e centraliza o log de todos os eventos MQTT no PostgreSQL.
2. **FastAPI Web API:** Serve o painel de controle e endpoints de status.
3. **Telegram Bot (Aiogram):** Interface móvel para controle e monitoramento (em desenvolvimento).
4. **Network Watchdog:** Script Bash para auto-recuperação do enlace MQTT/Rede.

## Infraestrutura de Backups
- **Armazenamento:** Cloudflare R2 (Object Storage).
- **Sincronizador:** `rclone`.
- **Backup:** Dumps SQL comprimidos e rotacionados automaticamente.
