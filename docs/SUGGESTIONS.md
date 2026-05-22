# Sugestões para Futuras Atualizações

Aqui estão algumas sugestões que considerei enquanto construíamos a base do projeto. Elas visam adicionar resiliência e novas funcionalidades ao Light Manager.

## 1. Monitoramento Inteligente (Health Check) no Bot
O bot do Telegram pode ser atualizado para ter um loop em background que verifica ativamente se os `ESP8266/Wemos` estão conectados. Como os Wemos agora enviam um sinal de `online` a cada 60 segundos no tópico de `/status`, o bot pode te alertar caso alguma placa pare de enviar esse heartbeat.

## 2. Cálculo Financeiro de Consumo (R$)
Como o banco de dados já possui o registro exato de `power_w` (potência nominal em Watts) de cada lâmpada e o tempo exato que ficaram ligadas, seria trivial criar uma variável no `.env` com a **tarifa da concessionária de energia da sua região (R$/kWh)**. Assim, a API e o Telegram poderiam te dizer em tempo real quanto as lâmpadas externas custaram no último mês.

## 3. Segurança Física no ESP
Como segurança caso a internet ou o Raspberry falhem enquanto você estiver viajando, podemos colocar um Sensor LDR (Módulo Fotossensor) nos ESPs, conectado às portas analógicas. O código em C++ poderia ter uma trava de segurança: "Se não recebi comandos MQTT por mais de 2 horas e está escuro, ligue as luzes sozinho".

## 4. Gerenciamento do Autômato Solar via Telegram
Expandir os botões do comando `/liga` do Telegram para permitir a ativação ou desativação da variável `auto_mode` no banco de dados. Isso permitiria a você pausar as automações de uma luz específica direto pelo celular, caso esteja dando uma festa no quintal ou queira controle manual.
