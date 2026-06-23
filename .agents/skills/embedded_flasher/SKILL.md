---
name: embedded_flasher
description: Compile, flash, and test ESP8266/Wemos D1 R1 microcontrollers using esptool and MQTT connection validation.
---

# Skill: Gravador de Firmware Embarcado (embedded_flasher)

Esta skill permite ao assistente gerenciar o processo de compilação, gravação e testes pós-flash do firmware do Wemos D1 R1 (ESP8266) deste repositório.

---

## ⚡ Fluxo de Trabalho do Agente

Quando o usuário solicitar a gravação do firmware, siga este roteiro estruturado:

### 1. Verificação Prévia de Hardware
Antes de iniciar a gravação, certifique-se de que a porta serial USB está ativa e acessível:
* Porta Padrão: `/dev/ttyUSB0`
* Verifique a presença do dispositivo USB executando:
  ```bash
  ls -l /dev/ttyUSB0
  ```
* Se o dispositivo não for encontrado, liste os barramentos USB com:
  ```bash
  lsusb
  dmesg | grep tty
  ```
* **Problema de Permissão:** Caso ocorra erro de permissão (ex: *Permission Denied*), instrua o usuário a ajustar o acesso ou adicione o usuário ao grupo correto:
  ```bash
  sudo chmod a+rw /dev/ttyUSB0
  # Ou adicionar ao grupo dialout (requer logout para surtir efeito)
  sudo usermod -a -G dialout $USER
  ```

### 2. Executar o Script de Flash
Uma vez confirmada a porta USB, execute a gravação utilizando o script utilitário localizado na pasta de scripts:
```bash
bash scripts/08_flash_wemos.sh
```

Monitore a saída do console para garantir que o `esptool` conclua com sucesso:
* Conexão estabelecida com o ESP8266.
* Limpeza e gravação do bloco de memória concluídas com `100%`.

### 3. Validação de Rede e Comunicação MQTT
O script de flash realiza testes automáticos pós-gravação. No entanto, valide manualmente se necessário:
* **Ping Test:** `ping -c 3 192.168.1.111` (IP estático configurado no firmware).
* **MQTT Test:** Verifique se as mensagens de transição e o Heartbeat estão chegando ao Broker rodando:
  ```bash
  mosquitto_sub -h 192.168.1.7 -u bruno -P blurbang -t "home/outdoor/status" -v
  ```
