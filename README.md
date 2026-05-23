# Light Manager

Este repositório contém a solução completa para o controle inteligente de iluminação externa residencial, projetado para operar com foco no minimalismo de recursos (RAM/CPU) em um Raspberry Pi 3B com Alpine Linux.

## 🚀 Funcionalidades
- 💡 **Controle Remoto:** Acione suas luzes pela Interface Web ou via Bot do Telegram (em desenvolvimento).
- 🌅 **Automação Solar Inteligente:** Ciclo circadiano baseado em latitude/longitude com GMT-3 (Brasília).
- 🛡️ **Resiliência Industrial:** 
    - **Watchdog de Rede:** Monitoramento via Ping e Banco de Dados; força reboot do Wemos se a conexão MQTT travar.
    - **NTP Fallback:** O firmware mantém o ciclo (18:00-05:00) mesmo sem conexão com o servidor.
    - **IP Estático:** Configuração direta no firmware para evitar dependência de DHCP.
- 📊 **Monitoramento:** Registro de eventos com metadados de origem (`mqtt_capture`, `solar_trigger`, `hourly_snapshot`).
- ☁️ **Backups Resilientes:** Dumps automáticos do PostgreSQL para o Cloudflare R2.

## 🛠️ Arquitetura
- **Hardware:** Wemos D1 R1 (ESP8266) + Relé 2 canais (Active Low).
- **Servidor:** Raspberry Pi 3B rodando Alpine Linux.
- **Protocolo:** MQTT (Mosquitto 2.0) com autenticação obrigatória.
- **Banco de Dados:** PostgreSQL 15+ com colunas `TIMESTAMPTZ` para precisão temporal.

## 📂 Organização do Repositório
Consulte a pasta `docs/` para aprofundar seu conhecimento na estrutura do projeto:
- `docs/STACK.md`: Tecnologias utilizadas.
- `docs/ROADMAP.md`: Próximos passos e status atual.
- `docs/BACKUP_MANUAL.md`: Instruções sobre os backups na nuvem.

## ⚙️ Como começar
1. Copie o arquivo `.env.example` para `.env` e ajuste suas senhas, coordenadas e o `WEMOS_IP`.
2. Siga os scripts enumerados na pasta `scripts/` para provisionar o ambiente.
3. Utilize o `crontab_template.txt` para configurar a persistência e os watchdogs no sistema.
4. **Firmware:** O código em `firmware/wemos_light/` deve ser compilado e carregado no Wemos.

---
**Nota de Resiliência:** O sistema utiliza `scripts/entrypoint.sh` para garantir que todos os serviços subam no boot do Raspberry Pi com os delays necessários para a rede estar pronta.
