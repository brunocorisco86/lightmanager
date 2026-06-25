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

---

## ⛅ 3. Implementações do Dia 22/06/2026 (Sincronização Meteorológica)

### 🌧️ Sincronização Inteligente de Offsets baseada em Cobertura de Nuvens
* **Demanda**: Ajustar dinamicamente os tempos de desvio (offsets) de ligar/desligar com base na cobertura de nuvens atual, para compensar a luminosidade natural reduzida em dias nublados/chuvosos.
* **Solução**: 
  - Desenvolvemos o script [scripts/weather_offset_sync.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/scripts/weather_offset_sync.py), que consulta a API do Open-Meteo para a previsão horária de cobertura de nuvens (`cloud_cover`) em Palotina (coordenadas do `.env`).
  - Implementamos interpolação linear dos desvios:
    - 0% de nuvens $\implies$ Ligar: +10 min / Desligar: -10 min
    - 100% de nuvens $\implies$ Ligar: -10 min / Desligar: +10 min
  - Atualizamos a tabela `light_points` no PostgreSQL com os novos offsets inteiros arredondados.
* **Testes e Comissionamento**:
  - Criamos a suíte de testes unitários [tests/test_weather_sync.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/tests/test_weather_sync.py) que roda com mocks do banco de dados e da API, garantindo robustez e permitindo rodar a suíte inteira localmente sem Docker (`pytest`).
  - Adicionamos a tarefa ao [crontab_template.txt](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/crontab_template.txt) para rodar automaticamente duas vezes ao dia (**05:00** e **17:00**).
  - Incluímos as dependências do Open-Meteo e análise de dados (`openmeteo-requests`, `requests-cache`, `retry-requests`, `numpy`, `pandas`, `pytz`, `bcrypt`) no [bot/requirements.txt](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/bot/requirements.txt) e nos scripts de setup ([setup.sh](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/scripts/setup.sh) / [00_setup_python.sh](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/scripts/00_setup_python.sh)).
* **Status**: Todo o código foi testado localmente, sincronizado para o repositório remoto Git (`origin/main`), implantado no servidor de produção `alpine`, onde as novas dependências foram instaladas e a tarefa do cron foi ativada com sucesso.

---

## 💡 4. Implementações do Dia 23/06/2026 (Consumo e Resiliência)

### 🔌 Correção do Desligamento Precoce da Luz (Bug de Limite NTP)
* **Falha**: A luz desligava prematuramente às 05:00 da manhã no horário de Brasília, antes do amanhecer previsto (ex: 07:21).
* **Causa Raiz**: O firmware do Wemos D1 R1 em [wemos_light.ino](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/firmware/wemos_light/wemos_light.ino) possuía a função `isNightTime()` com um limite estático inferior de `5` (`tm_hour < 5`). Ao bater 05:00, o Wemos considerava que era dia e forçava os pinos dos relés para `OFF` fisicamente, sem publicar o estado de volta ao MQTT broker.
* **Solução**: 
  - Ajustamos a função `isNightTime()` para aceitar o limite até as 08:00 (`tm_hour < 8`), cobrindo o nascer do sol no inverno brasileiro.
  - Implementamos publicação de estado `OFF` via MQTT na rotina física de fallback do Wemos se ele desligar as luzes de forma forçada.
  - Alteramos no cron do Raspberry Pi a sincronização de nuvens de **05:00** para **02:00** (depois da meia-noite) em [crontab_template.txt](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/crontab_template.txt) para que a alteração de offsets não conflite com a mudança de estado física.

### 📊 Registro de Duração e Consumo de Energia em kWh
* **Demanda**: Medir a quantidade de tempo em que a iluminação ficou ativa e estimar o consumo em kWh para relatórios e análises no painel.
* **Solução (Banco & Backend)**:
  - Criamos a tabela `light_consumption` no PostgreSQL (atualizando o inicializador [05_register_lights.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/scripts/05_register_lights.py)).
  - Ajustamos o [solar_worker.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/scripts/solar_worker.py) para monitorar transições para `OFF`. No desligamento de qualquer ponto, ele calcula a diferença temporal em relação ao último status `ON`, busca a potência nominal (`power_w`) e registra o tempo ativo e os kWh consumidos: $\text{kWh} = \frac{\text{segundos}}{3600} \times \frac{\text{power\_w}}{1000}$.
  - Criamos a rota de API `/api/history/consumption` em [main.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/web_api/main.py) retornando as estatísticas diárias consolidadas.
* **Solução (Frontend)**:
  - Refatoramos [index.html](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/web/index.html) e [style.css](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/web/style.css) para exibir dois gráficos responsivos lado a lado.
  - Atualizamos [script.js](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/web/script.js) para gerar gráficos interativos com Chart.js:
    - **Gráfico 1**: Duração diária ligada por lâmpada de forma empilhada (stacked).
    - **Gráfico 2**: Consumo diário consolidado em kWh na cor verde-esmeralda.

### 🛡️ Fallback Local de Cronograma no Firmware (Wemos Offline)
* **Demanda**: Garantir que as luzes liguem e desliguem mesmo se o Raspberry Pi ou o Broker caírem temporariamente.
* **Solução**:
  - No `solar_worker.py`, implementamos o cálculo diário do horário de fallback (pôr do sol + 15 min para ligar, nascer do sol + 15 min para desligar) que é publicado de hora em hora nos tópicos `home/outdoor/fallback/on` e `home/outdoor/fallback/off` como mensagens retidas (`retain=True`).
  - No firmware `wemos_light.ino`, adicionamos o recebimento e armazenamento local desse cronograma. Caso o Wemos detecte perda de comunicação com o broker MQTT (`!client.connected()`), ele assume o acionamento e desligamento local baseado nos horários e no relógio NTP do ESP8266.
    - A função `isNightTime()` do Wemos foi ajustada para aceitar essa tabela dinâmica quando disponível, evitando concorrência com o acionador real.

---

## ⚡ 5. Implementações do Dia 24/06/2026 (Time Sync Híbrido, Rollover e Tarifas ANEEL)

### ⏰ Sincronização de Tempo Híbrida (Remoção do NTP no Embarcado)
* **Demanda:** Evitar que a biblioteca SNTP em background do ESP8266 limpe o offset de fuso horário local e reverta o relógio para UTC após quedas ou oscilações de conexão de rede.
* **Solução:**
  - Removemos totalmente as consultas diretas a servidores NTP do código do [wemos_light.ino](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/firmware/wemos_light/wemos_light.ino).
  - Configuramos a placa apenas com a string POSIX de fuso horário permanente: `configTime("<-03>3", nullptr)`.
  - O sincronismo de tempo passou a operar de forma 100% local através do envio de payloads Unix Epoch pelo Solar Worker para o tópico MQTT `home/outdoor/time` a cada minuto, com o Wemos ajustando o relógio via chamada de sistema `settimeofday`.

### ⚡ Correção de Duração Truncada por Reforço Horário
* **Falha:** O consumo total do dia 23/06 estava subestimado no banco (0,0284 kWh em vez de ~0,11 kWh) por registrar durações muito baixas.
* **Causa Raiz:** O envio de mensagens `ON` redundantes de hora em hora (para garantir resiliência contra falhas do receptor) criava múltiplos eventos de acendimento sequenciais no banco sem interposição de `OFF`. A query antiga simplesmente computava o tempo a partir do último `ON` (que era a mensagem de reforço mais recente), descartando as horas de uso anteriores.
* **Solução:**
  - Refatoramos a query em `log_event_to_db` no [solar_worker.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/scripts/solar_worker.py) para buscar o **primeiro** `ON` real ocorrido após o último `OFF` faturado no banco. Com isso, os disparos de reforço horário não truncam mais as durações reais acumuladas dos ciclos.

### 🌙 Mecanismo de Virada de Dia (Rollover)
* **Demanda:** Fracionar o tempo e custo das luzes que permanecem ativas durante a madrugada de forma que a estatística de uso seja separada exatamente entre os dois dias correspondentes.
* **Solução:**
  - Criamos a função `run_day_rollover()` executada às **23:59:59** no [solar_worker.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/scripts/solar_worker.py).
  - Ela calcula e registra o consumo ativo do ponto até o limite do dia corrente, insere um evento `OFF` virtual e, logo em seguida, insere um evento `ON` virtual datado para `00:00:00` do dia seguinte para dar continuidade à contagem de tempo.

### 💰 Integração Tarifária e Financeira (ANEEL & Impostos)
* **Demanda:** Calcular o custo financeiro estimado em Reais (R$) do consumo da iluminação nos relatórios e no painel administrativo.
* **Solução:**
  - Desenvolvemos o script utilitário [scripts/tariff_sync.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/scripts/tariff_sync.py) que consulta a API CKAN de Dados Abertos da ANEEL, localiza e baixa dinamicamente a última planilha de tarifas homologadas das concessionárias e faz o upsert dos valores das tarifas TE e TUSD do grupo Residencial convencional (B1) na tabela `energy_tariffs` do PostgreSQL.
  - Atualizamos a geração do relatório diário [reports/generate_daily.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/reports/generate_daily.py) para incluir a projeção de custo financeiro caso as variáveis de distribuidora e imposto estejam parametrizadas no `.env`.
	- Desenvolvemos a rota de API `/api/consumption/monthly` em [web_api/main.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/web_api/main.py) e criamos um widget de resumo financeiro e consumo mensal na interface web do painel. Configurado o `.env` de produção com o slug `copel-dis` e taxa de imposto estimada em 25% (`ENERGY_TAX_RATE=0.25`).

---

## ⚡ 6. Implementações do Dia 25/06/2026 (Persistência de Override Manual e Correção de Oscilação de Fallback)

### 🔄 Correção de Oscilação ao Ligar (Conflito de Fallback e Trigger Solar)
* **Falha:** As luzes ligavam próximo das 18:10 (Gatilho Solar) e ficavam alternando entre ON/OFF em intervalos curtos de ~30 a 60 segundos até as 18:13, quando finalmente estabilizavam ligadas.
* **Causa Raiz:** O Solar Worker calculava e enviava um horário fixo de fallback de ligar no início da noite como `sunset + 15 minutos` (18:13), enquanto os pontos de iluminação reais estavam programados para ligar antes (ex: 18:08, devido ao desvio do clima). Quando as luzes ligavam às 18:08, o microcontrolador Wemos realizava a verificação de saúde a cada 60 segundos e, por ainda estar antes de 18:13, avaliava o horário como "dia" (`!isNightTime()`), desligando forçosamente os relés fisicamente e enviando o estado `OFF` via MQTT. O Solar Worker capturava o `OFF`, comparava com seu estado desejado (`ON`) e reenviava o comando `ON` via MQTT para corrigir o desvio, iniciando o ciclo de oscilações até a hora do fallback bater 18:13.
* **Solução:**
  - **Cálculo Dinâmico de Fallback:** Refatoramos a lógica de cálculo de horários de fallback em [solar_worker.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/scripts/solar_worker.py). Agora, ele busca dinamicamente todos os pontos de luz automáticos ativos e define o fallback de ligar como 1 minuto antes do ponto que liga mais cedo (`min(offset_on) - 1`), e o de desligar como 1 minuto após o que desliga mais tarde (`max(offset_off) + 1`). Isso garante que o Wemos nunca force um desligamento durante a janela de operação agendada.
  - **Correção Definitiva no Firmware:** Atualizamos a função de verificação do Wemos em [wemos_light.ino](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/firmware/wemos_light/wemos_light.ino). A partir de agora, o dispositivo só executará reações unilaterais e forçadas de desligamento diurno se estiver desconectado do Broker MQTT (`!client.connected()`). Estando conectado, ele confia plenamente nos comandos e no estado enviado pela API e pelo Solar Worker.

### 💾 Persistência de Decisão (Override Manual)
* **Demanda:** Garantir que se o usuário ligar ou desligar as luzes manualmente via API (interface web) ou Bot do Telegram, esse estado manual prevaleça e não seja sobrescrito pelo ciclo de reforço de estado automático do Solar Worker.
* **Solução:**
  - Criamos a coluna `manual_override` (tipo `VARCHAR(10)`) na tabela `light_points` no PostgreSQL.
  - Ajustamos o script de inicialização e migração [scripts/05_register_lights.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/scripts/05_register_lights.py) para criar a coluna e rodar a migração `ALTER TABLE` de forma retroativa e automática.
  - Atualizamos a rota de comando da API FastAPI em [web_api/main.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/web_api/main.py) e o callback de bot em [bot/bot.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/bot/bot.py) para que, em todo acionamento manual, eles atualizem `manual_override = 'ON'` ou `'OFF'` e salvem o evento sob a fonte `manual_control`.
  - No [solar_worker.py](file:///home/bruno/Documentos/4_HOMELAB/9_LIGHT_MANAGER/scripts/solar_worker.py), a lógica de automação agora respeita o `manual_override` do banco de dados (se preenchido, torna-se o `desired_state`), suspendendo o controle solar para aquela lâmpada temporariamente.
  - O `manual_override` é redefinido automaticamente para `NULL` (limpando o override) no momento exato em que o próximo gatilho solar do ciclo oposto (`target_on_str` ou `target_off_str`) ocorrer, restaurando a rotina de automação padrão sem intervenção do usuário.
