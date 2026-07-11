# Light Manager - Roadmap & Next Steps

## 1. Concluído ✅
- Estrutura base de diretórios e arquitetura industrial.
- Modelagem do Banco de Dados (Suporte a múltiplos pontos de luz e offsets solares).
- Scripts de relatórios diários (CSV/JSON export via psql).
- Interface Web (Vanilla JS + FastAPI).
- Automação Solar inteligente (Solar Worker com GMT-3, retry e cache).
- Rotina de Backup otimizada e resiliente para o Cloudflare R2 (Rclone).
- Firmware Resiliente (Active Low, NTP Fallback, IP Estático e Comando de Reboot).
- Watchdog de Rede (Auto-cura via Ping e análise de logs do DB).
- Centralização de execução via `scripts/entrypoint.sh` e `crontab_template.txt`.
- Configurar o Raspberry Pi 3B com Alpine Linux e clonar este repositório.
- Rodar a sequência de scripts `./scripts/00_...` até `./scripts/05_...` no Raspberry.
- Configurar o Crontab no Raspberry Pi para ativação automática.
- Finalizar e testar o Bot Telegram (`bot/bot.py`).
- Criar a tabela `light_consumption` e lógica de backend/MQTT no `solar_worker.py` para registrar a duração da luz ativa (tempo ligada) e os kWh consumidos a cada transição para desligado (`OFF`).
- Desenvolver gráficos de estatísticas no frontend (empilhado por lâmpada para horas ligadas e consumo diário em kWh).
- Implementação de fallback local de horários no firmware (Wemos D1 R1) integrado a comandos de fallback solares enviados via MQTT com retain (garantindo funcionamento autônomo offline em caso de quedas do Raspberry/broker).

## 2. Next Steps (Para Comissionamento) 🚧
- [ ] Gravar o Firmware atualizado (`firmware/wemos_light/wemos_light.ino`) nas placas Wemos D1/ESP8266.

## 3. To-Do (Melhorias Futuras) 🛠️

### 🤖 Bot Telegram
- [ ] Implementar monitoramento de "saúde" do Raspberry Pi no Bot (CPU/Temp/RAM).
- [ ] Monitoramento Inteligente (Health Check) de placas Wemos: loop em background que verifica se as placas enviaram o heartbeat no tópico `/status` (a cada 60s) e alerta em caso de queda.
- [ ] Expandir comandos do Telegram (como `/liga`) para ativar ou desativar o modo automático (`auto_mode`) de um ponto de luz diretamente pelo chat.
- [ ] Enviar relatório sintético mensal todo dia 5 contendo a média de acionamentos, média de consumo diário por tópico e limites horários de ativação.

### 📊 Painel & Relatórios (Frontend/Backend)
- [ ] Implementar o somatório de consumo mensal acumulado no painel frontend e nos relatórios.
- [ ] Integração com concessionária para cálculo de custo real em R$ baseando-se na tarifa configurada localmente ou consultada via API.
- [ ] Adicionar no site a exibição do SLA do sistema (disponibilidade dos dispositivos e serviços).

### ⚙️ Integração & Resiliência
- [ ] Modo de "Simulação de Presença": acendimento randômico em horários programados quando em férias.
- [ ] Integração nativa com Home Assistant via MQTT Discovery.
- [ ] Segurança Física local no Wemos usando Sensor LDR: se o dispositivo perder comunicação com o broker MQTT por mais de 2 horas e estiver escuro, aciona o relé localmente de forma autônoma.
