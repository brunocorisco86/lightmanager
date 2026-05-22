# Stack do Sistema - Light Manager

## Arquitetura e Hardware
- **Cérebro:** Raspberry Pi 3B
- **SO Principal:** Alpine Linux (escolhido por seu minimalismo, usando musl e BusyBox).
- **Atuadores:** Wemos D1 (ESP8266) com módulos Relé.

## Software e Comunicação
- **Broker MQTT:** Eclipse Mosquitto (Instalado de forma nativa no Alpine via `apk` para máxima economia de RAM, sem uso de Docker para este serviço).
- **Protocolo IoT:** MQTT (Publisher/Subscriber).

## Persistência de Dados
- **Banco de Dados:** PostgreSQL 15 (Rodando via Docker).
- **Esquema Inicial:** Duas tabelas principais (`light_points` para configurações de hardware e auto_mode; `light_events` para o registro temporal da iluminação).

## Lógica, Interface e Automação
Toda a lógica está contida no ambiente virtual Python (`.venv`):
1. **Bot do Telegram (`bot.py`):** Feito com `aiogram` assíncrono. Interface de linha de comando remota para gerenciar o sistema e checar a saúde (`psutil`).
2. **Web API (`main.py`):** Feito com `FastAPI`. Servidor estático e de endpoints extremamente leve e rápido.
3. **Frontend (`index.html`, `script.js`):** Vanilla Javascript + Chart.js via CDN. Sem frameworks pesados ou processos de build.
4. **Autômato Solar (`solar_worker.py`):** Script em Python que faz fetch diário da API (com retenção em `sun_cache.json`), calcula os offsets do banco e envia sinais ao MQTT.

## Infraestrutura de Backups
- **Armazenamento Secundário:** Cloudflare R2 (Compatível com S3 e sem custo de Egress/Saída).
- **Sincronizador:** `rclone` (Instalação via Alpine apk).
- **Política de Retenção:** Mantém sempre as últimas 3 cópias no bucket via script (`scripts/backup_r2.sh`).
