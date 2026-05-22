# Conter light manager

Este repositoio se destina a criar uma solução caseira para o controle de iluminação externa de uma casa
- ligando durante a noite e desligando durante o dia

## Stack software
- MQTT (mosquitto) para receber os comandos de liga e desliga
- Site 
	(host local) para ligar e desligar as lampadas, assim como ver o historico em que ficou ligado/desligado
- PostgreSQL
	para registrar os instante de ligar e desligar das lampadas, registrar o tempo de funcionamento, potencia nominal das lampadas, consumo de energia estimado
- Backup
	Bucket R2 da Cloudflare que eu tenho conta (mensalmente)
- Python (para o que for preciso) - Com venv
	bot telegram para verbosidade
	bot para ligar e desligar a lampada (receber e dar comandos pelo telegram)
- Autenticação
	Telegram
- Docker / Docker compose
	Bot telegram
	Postgres
- Cron
	Subir site
	Bot
	Relatórios diários

## Stack hardware
- Raspberry Pi 3B com alpine linux
- 1 Wemos D2 com modulo rele
- ESP32 (modelo indefinido)

## Resultados esperados
	Site para conferir, dar comandos MQTT, ver graficos da base Postgres
	Bot telegram (aiogram) para conferir estado, dar comandos 
	Backup no R2
	Automação

## IDE
	Gemini-Cli
	Arduino IDE

## Premissas
	Minimalismo no gasto de RAM
	Verbosidade (Log e telegram)
	Crie .env e variáveis de ambiente
