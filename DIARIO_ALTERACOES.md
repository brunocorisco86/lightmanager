# Diário de Alterações (Changelog) - 21/06/2026

Este documento registra as falhas diagnosticadas no ambiente de produção do **Light Manager** no dia 21 de junho de 2026, juntamente com as correções e melhorias aplicadas no repositório.

---

## 🔍 1. Problemas Identificados (Erros em Produção)

### 🤖 Telegram Bot Inativo
* **Falha**: O bot do Telegram caiu no dia **21/06/2026 às 09:37:49** após um erro temporário de resolução de DNS (`ClientConnectorDNSError`) ao tentar consultar a API do Telegram (`api.telegram.org:443`).
* **Causa Raiz**: O watchdog do crontab disparou corretamente, mas o script `restart_bot.sh` antigo não carregava as dependências virtuais do Python `.venv` em seu escopo de execução direta. Além disso, a chamada indireta via `entrypoint.sh` falhava silenciosamente no ambiente restrito do `cron`.

### 🔌 Dispositivo Wemos Sem Comunicação (MQTT Timeout)
* **Falha**: A placa Wemos D1 R1 (ESP8266) caiu exatamente no mesmo minuto (**09:37:48**), registrando um estouro de KeepAlive no broker Mosquitto (`exceeded timeout, disconnecting`).
* **Causa Raiz**: O Wemos respondia a pings de rede normalmente (pois o firmware do ESP8266 lida com ICMP de forma nativa e em baixo nível), mas o loop principal de controle MQTT travou ou perdeu a conexão com o socket sem se restabelecer. O reboot preventivo via MQTT do watchdog não funcionava porque a placa já estava desconectada do broker.

### 📅 Erros Críticos de Script Inexistente no Cron
* **Falha**: Erros repetitivos no log do cron indicando que `/home/bruno/lightmanager/reports/generate_daily.sh` não existia no repositório, inviabilizando a geração de relatórios diários de consumo que estavam agendados para as 23:55.

---

## 🛠️ 2. Melhorias e Correções Implementadas

### 1. Refatoração do Watchdog do Bot do Telegram
* **Implementação**: Reescrevemos o script [scripts/restart_bot.sh](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/scripts/restart_bot.sh). Ele agora ativa o ambiente virtual `.venv` de forma explícita e inicia o Python diretamente redirecionando os outputs para o arquivo de log do bot (`logs/bot.log`).
* **Status**: Testado e implantado em produção. O bot do Telegram (PID: `5967`) está online e operando em Long Polling com sucesso.
* **Logs do Cron**: O script de agendamento [crontab_template.txt](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/crontab_template.txt) foi ajustado para redirecionar erros do watchdog do bot para `logs/cron.log`. O crontab de produção foi atualizado.

### 2. Criação do Watchdog Local de Firmware (Resiliência do Wemos)
* **Implementação**: Adicionamos lógica de autocura direto na placa em [wemos_light.ino](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/firmware/wemos_light/wemos_light.ino):
  - Criadas variáveis para rastrear o tempo de conexão bem-sucedida do WiFi e MQTT (`lastWiFiConnected` e `lastMqttConnected`).
  - Caso a placa fique sem conexão WiFi ou sem conexão com o Broker MQTT por **mais de 10 minutos**, ela executará um reinício via software de forma independente (`ESP.restart()`).
  - Isso garante que a placa se recupere sozinha de falhas de rede.

### 3. Desenvolvimento do Relatório Diário de Consumo via Telegram
* **Implementação**: Desenvolvemos e configuramos o script de relatórios de consumo diário:
  - [reports/generate_daily.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/reports/generate_daily.py): Script Python que consulta o PostgreSQL e realiza um cálculo avançado de interseção de intervalos de tempo para somar as horas ativas de cada lâmpada no dia corrente. Também calcula a estimativa de consumo de energia em **kWh** (utilizando a potência nominal `power_w` configurada).
  - [reports/generate_daily.sh](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/reports/generate_daily.sh): Wrapper em bash para ativar o `.venv` e executar o script Python.
* **Status**: Implantado e testado em produção com sucesso (mensagem enviada com êxito via Telegram Bot API). Executará automaticamente às **23:55** diariamente.
