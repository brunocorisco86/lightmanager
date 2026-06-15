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

## 🛡️ Mecanismos de Confiabilidade & Testes Locais

Para garantir a operação contínua do sistema e facilitar o desenvolvimento de novas features, o Light Manager dispõe de mecanismos de confiabilidade de hardware e testes locais avançados.

### 🧪 Como Rodar a Suíte de Testes Localmente
Os testes de integração necessitam de uma instância do banco PostgreSQL disponível para validação real dos fluxos de banco de dados e autenticação:

1. **Suba a infraestrutura do banco de testes local (Docker)**:
   ```bash
   docker-compose up -d
   ```
2. **Inicialize as tabelas do banco de dados local**:
   ```bash
   .venv/bin/python3 -c "import importlib; rl = importlib.import_module('scripts.05_register_lights'); rl.init_db(); import scripts.manage_users as mu; mu.init_users_table()"
   ```
3. **Execute os testes**:
   ```bash
   ./run_tests.sh
   ```
   *Nota: O script de testes detecta se ferramentas acessórias como o `rclone` ou o `docker` estão ausentes no PATH e pula testes relacionados a eles de forma limpa.*

### ⚙️ Funcionalidades de Resiliência de Automação
* **Acionamento Físico Direto (Firmware)**: O código embarcado do Wemos [wemos_light.ino](file:///media/brunoconter/DOCUMENTOS3/10_LIGHT_MANAGER/lightmanager/firmware/wemos_light/wemos_light.ino) força o estado elétrico dos relés de forma incondicional em cada comando MQTT de entrada. Isso evita que ruídos físicos façam a leitura lógica de `digitalRead` impedir acionamentos corretos.
* **Reforço de Estado Horário (Lazy & Thread-safe)**: O script [solar_worker.py](file:///media/brunoconter/DOCUMENTOS3/10_LIGHT_MANAGER/lightmanager/scripts/solar_worker.py) envia o estado solar desejado (com QoS 1 e Retain) de forma proativa a cada virada de hora e na inicialização do serviço, servindo de fallback para quedas de energia no ESP8266. A inicialização preguiçosa do pool de conexões é protegida contra concorrência por Locks.
* **Checagem Preventiva de Saúde (Telegram Alertas)**: O `solar_worker` confere se o Wemos está comunicando com o broker Mosquitto exatamente **5 minutos antes** de cada pôr ou nascer do sol. Caso o Wemos esteja offline há mais de 3 minutos, um alerta urgente com tag `🚨 ALERTA DE SAÚDE EMBARCADO` é disparado via Telegram.
* **Logs Enriquecidos**: Todas as transições de status capturadas via broker MQTT são armazenadas em disco sob a pasta `/logs/` de forma explícita com o payload correspondente para diagnósticos simplificados.

## 📂 Organização
- `docs/R2_BACKUP_SETUP.md`: Configuração do Cloudflare R2.
- `web/`: Interface frontend (HTML/CSS/JS).
- `web_api/`: Servidor de API e rotas administrativas.
- `requirements.txt`: Dependências consolidadas do projeto.

---
**Nota Técnica:** O sistema utiliza `TIMESTAMPTZ` no PostgreSQL para garantir que todos os eventos sejam registrados com a precisão de Brasília (GMT-3), evitando desvios em relatórios de consumo.
