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
- Implementar monitoramento de "saúde" do Raspberry Pi no Bot (CPU/Temp/RAM).
- Adicionar modo de "Simulação de Presença" (acendimento randômico em horários programados quando em férias).
- Integração com Home Assistant via MQTT Discovery.
- Enviar relatório sintético mensal todo dia 5 contendo:
  - Média de acionamentos ao dia.
  - Média de consumo por dia por tópico.
  - Horário mínimo e máximo de ligar e desligar.
- Adicionar no site a exibição do SLA do sistema (disponibilidade dos dispositivos e serviços).

