---
name: embedded_flasher
description: Compile, flash, and test ESP8266 (Wemos D1 R1) and ESP32-C3 Supermini microcontrollers using arduino-cli, esptool, and MQTT connection validation.
---

# Skill: Gravador de Firmware Embarcado (embedded_flasher)

Esta skill permite ao assistente gerenciar o processo de compilação, gravação e testes pós-flash dos microcontroladores do Light Manager:
1. **Wemos D1 R1 (ESP8266)**: Fachada (`pinFrente = D1`) e Fundos (`pinFundos = D2`) - IP: `192.168.1.111`.
2. **ESP32-C3 Supermini**: Muro (`pinMuro = GPIO4`), Auxiliar (`pinAux = GPIO5`) e LED (`GPIO8`) - IP: `192.168.1.112`.

---

## ⚡ Fluxo de Trabalho do Agente

Quando o usuário solicitar a gravação do firmware, siga este roteiro estruturado:

### 1. Verificação Prévia de Hardware
Antes de iniciar a gravação, certifique-se de que a porta serial USB está ativa e acessível:
* **ESP32-C3 Supermini:** Usa USB CDC/JTAG nativo, geralmente alocado em `/dev/ttyACM0` ou `/dev/ttyACM1`.
* **Wemos D1 R1 (ESP8266):** Usa chip CH340 USB-Serial, geralmente em `/dev/ttyUSB0` ou `/dev/ttyUSB1`.
* Verifique a presença do dispositivo USB executando:
  ```bash
  ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
  esptool chip-id
  ```
* Se o dispositivo não for encontrado, liste os barramentos USB com:
  ```bash
  lsusb
  dmesg | tail -n 20
  ```
* **Permissão Serial:** Se ocorrer *Permission Denied*:
  ```bash
  sudo chmod a+rw /dev/ttyACM0 # ou /dev/ttyUSB0
  ```

### 2. Executar o Script Unificado de Flash
Execute a gravação passando o identificador da placa desejada:
```bash
# Para gravar o ESP32-C3 Supermini (Muro & Auxiliar):
bash scripts/08_flash_firmware.sh 2

# Para gravar o Wemos D1 R1 (Fachada & Fundos):
bash scripts/08_flash_firmware.sh 1
```

O script utilitário realiza automaticamente:
1. Detecção automática da porta serial.
2. Identificação do chip conectado (`ESP32-C3` ou `ESP8266`).
3. Compilação automática sob demanda com `arduino-cli`.
4. Gravação física em alta velocidade (`460800` baud).
5. Testes automatizados pós-flash:
   - Ping no IP estático (`192.168.1.112` ou `192.168.1.111`).
   - Disparo de comandos MQTT (`ON`/`OFF`) e confirmação de resposta ACK em tempo real.

### 3. Dicas de Bootloader no ESP32-C3 Supermini
- Geralmente o CDC nativo entra em modo de download automaticamente via DTR/RTS.
- Caso o `esptool` trave aguardando conexão (*Connecting...*):
  1. Pressione e mantenha o botão **BOOT** (GPIO9).
  2. Pressione e solte o botão **RST** (Reset).
  3. Solte o botão **BOOT**.
  4. A placa estará em modo ROM Bootloader e aceitará o flash imediatamente.
