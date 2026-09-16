---
name: embedded_flasher
description: Compile, flash, and test ESP8266/Wemos D1 R1 and ESP32-C3 SuperMini microcontrollers using arduino-cli, esptool, and MQTT connection validation.
---

# Skill: Gravador de Firmware Embarcado (embedded_flasher)

Esta skill permite ao assistente gerenciar o processo de compilação, gravação e testes pós-flash de microcontroladores do repositório:
1. **Wemos D1 R1 (ESP8266):** Controle dos relés de iluminação externa (Frente, Fundos, Muro).
2. **ESP32-C3 SuperMini (RISC-V):** Leitura de presença do radar mmWave LD2420 e acionamento MQTT com temporizador de 2 minutos.

---

## ⚡ 1. Fluxo Wemos D1 R1 (ESP8266)

* **Porta Típica:** `/dev/ttyUSB0` (Driver CH340).
* **Script de Flash:**
  ```bash
  bash scripts/08_flash_wemos.sh
  ```
* **Validação:** Ping em `192.168.1.111` e tópico `home/outdoor/status`.

---

## ⚡ 2. Fluxo ESP32-C3 SuperMini (RISC-V + Radar LD2420)

### Características de Hardware
* **Interface USB:** USB CDC Nativo JTAG/Serial (`/dev/ttyACM0` ou `/dev/ttyACM1`, ID `303a:1001`).
* **Flags de Compilação Obrigatórias:**
  `build.extra_flags=-DARDUINO_USB_MODE=1 -DARDUINO_USB_CDC_ON_BOOT=1` (permite uso de `Serial.begin(115200)` via USB nativo).
* **Pinagem com Sensor Radar LD2420:**
  - VCC -> 3V3
  - GND -> GND
  - OUT -> GPIO 2 (`pinMode(2, INPUT_PULLDOWN)`)
  - TX -> GPIO 20 (`Serial1` RX)
  - RX -> GPIO 21 (`Serial1` TX)
  - LED Onboard -> GPIO 8 (Active LOW)

### Roteiro de Gravação
1. Verifique se o dispositivo está conectado:
   ```bash
   ls -l /dev/ttyACM*
   ```
2. Execute o script automatizado de compilação, flash e validação MQTT:
   ```bash
   bash scripts/09_flash_esp32c3.sh
   ```
3. Se a placa não entrar no modo de gravação automaticamente:
   - Pressione e segure o botão **BOOT** (GPIO 9).
   - Dê um clique no botão **RESET**.
   - Solte o botão **BOOT**.
   - Reexecute o script de flash.

### Monitoramento Serial ao Vivo
Para observar os pulsos de detecção de pessoas em tempo real:
```bash
arduino-cli monitor -p /dev/ttyACM0 -c baudrate=115200
```

