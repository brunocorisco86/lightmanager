# Light Manager

Este repositório contém a solução completa para o controle inteligente de iluminação externa residencial, projetado para operar com foco no minimalismo de recursos (RAM/CPU) em um Raspberry Pi 3B com Alpine Linux.

## 🚀 Funcionalidades
- 💡 **Controle Remoto:** Acione suas luzes pela Interface Web ou via Bot do Telegram.
- 🌅 **Automação Solar Inteligente:** Ciclo circadiano baseado em latitude/longitude com GMT-3 (Brasília).
- 🤖 **Controle via Telegram:** Comandos `/status`, `/liga` e `/desliga` com feedback em tempo real (Long Polling).
- ⚙️ **Gerenciamento Web:** Interface administrativa protegida por senha para cadastrar pontos, ajustar offsets de tempo e auditar o histórico solar.
- 🛡️ **Segurança & Resiliência:** 
    - **Login Seguro:** Autenticação via BCrypt com usuários persistidos no PostgreSQL.
    - **Watchdogs (Autocura):** Monitoramento triplo (API, Solar e Bot) a cada 15 min via Crontab.
    - **Persistência Pós-Reboot:** Escalonamento de boot via `@reboot` para garantir ordem de serviços.
    - **NTP & DNS Watchdogs:** Sincronização horária e diagnósticos de rede automáticos.
- 📊 **Monitoramento:** Registro detalhado de eventos e gráfico de consumo semanal.
- ☁️ **Backups Cloud:** Dumps automáticos para Cloudflare R2 (Mensal) com política de retenção.

## 🚀 Operação em Produção (Alpine Linux)
Para garantir que o sistema opere de forma resiliente no Raspberry Pi:

1. **Configurar Resiliência:** 
   ```bash
   # Aplica o template de crontab otimizado
   crontab crontab_template.txt
   ```
2. **Gerenciar Serviços Manualmente:**
   - Reiniciar tudo: `bash scripts/restart_api.sh && bash scripts/restart_solar.sh && bash scripts/restart_bot.sh`
   - Verificar Status: `pgrep -af python`
   - Logs em Tempo Real: `tail -f logs/*.log`

## 🛠️ Arquitetura
- **Hardware:** Wemos D1 R1 (ESP8266) + Relé 2 canais (Active Low).
- **Servidor:** Raspberry Pi 3B rodando Alpine Linux.
- **Backend:** FastAPI (Python 3.12) + Aiogram (Telegram) + Mosquitto MQTT.
- **Banco de Dados:** PostgreSQL 15+ (Porta 5433) com integridade de fuso horário.

## ⚙️ Gestão e Manutenção
O sistema possui scripts dedicados para operação contínua:
- **Reiniciar Serviços:** `bash scripts/restart_api.sh`, `bash scripts/restart_solar.sh` e `bash scripts/restart_bot.sh`.
- **Gestão de Usuários:** `python3 scripts/manage_users.py` (para criar/gerenciar acessos web).
- **Comissionamento:** `bash scripts/setup.sh` seguido da configuração do `.env`.

## 🧪 Testes de Integridade
Para validar toda a infraestrutura (API, Banco, Auth, MQTT, Telegram, Backup):
```bash
./run_tests.sh
```
O script executa **27 testes automatizados** que garantem que nenhuma alteração quebrou o fluxo de segurança ou automação.

## 📂 Organização
- `docs/R2_BACKUP_SETUP.md`: Configuração do Cloudflare R2.
- `web/`: Interface frontend (HTML/CSS/JS).
- `web_api/`: Servidor de API e rotas administrativas.
- `requirements.txt`: Dependências consolidadas do projeto.

---
**Nota Técnica:** O sistema utiliza `TIMESTAMPTZ` no PostgreSQL para garantir que todos os eventos sejam registrados com a precisão de Brasília (GMT-3), evitando desvios em relatórios de consumo.
