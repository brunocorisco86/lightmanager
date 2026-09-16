// ==========================================================
// TESTE PURO E MINIMALISTA - ESP32-C3 + RADAR LD2420
// Sem Wi-Fi, Sem MQTT, Sem Delay Bloqueante
// ==========================================================

const int PIN_PRESENCA = 2;   // Pino ligado ao OT1 ou OT2 do sensor
const int PIN_LED      = 8;   // LED azul onboard do ESP32-C3 SuperMini (Active LOW)
const int PIN_RADAR_RX = 20;  // RX do ESP32-C3 ligado ao TX do sensor
const int PIN_RADAR_TX = 21;  // TX do ESP32-C3 ligado ao RX do sensor

int ultimoEstado = -1;
unsigned long tempoMudanca = 0;
unsigned long ultimoPrint = 0;

void setup() {
  // Inicializa USB CDC Serial nativa do ESP32-C3
  Serial.begin(115200);
  delay(1000);

  pinMode(PIN_PRESENCA, INPUT_PULLDOWN);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, HIGH); // Apagado (Active LOW)

  // Inicializa UART com o LD2420 a 256000 baud
  Serial1.begin(256000, SERIAL_8N1, PIN_RADAR_RX, PIN_RADAR_TX);

  Serial.println("\n=============================================");
  Serial.println("🎯 TESTE DIRETO DE BANCADA - RADAR LD2420");
  Serial.println("Pino de Presenca: GPIO 2");
  Serial.println("LED Indicador:    GPIO 8 (Onboard)");
  Serial.println("=============================================\n");
}

void loop() {
  unsigned long agora = millis();
  int estadoAtual = digitalRead(PIN_PRESENCA);

  // 1. Espelhamento Imediato no LED onboard
  if (estadoAtual == HIGH) {
    digitalWrite(PIN_LED, LOW); // Acende LED onboard
  } else {
    digitalWrite(PIN_LED, HIGH); // Apaga LED onboard
  }

  // 2. Imprime na hora em que o estado mudar
  if (estadoAtual != ultimoEstado) {
    unsigned long duracao = agora - tempoMudanca;
    if (estadoAtual == HIGH) {
      Serial.printf("⚡ [MUDANCA] -> PRESENCA (HIGH)! Ficou LOW por %lu ms\n", duracao);
    } else {
      Serial.printf("⚪ [MUDANCA] -> REPOUSO  (LOW)!  Ficou HIGH por %lu ms\n", duracao);
    }
    ultimoEstado = estadoAtual;
    tempoMudanca = agora;
  }

  // 3. Status periódico a cada 500ms
  if (agora - ultimoPrint >= 500) {
    ultimoPrint = agora;
    Serial.printf("[STATUS] GPIO 2: %d | LED: %s | Duracao no estado: %lu ms\n",
                  estadoAtual,
                  (estadoAtual == HIGH) ? "ACESO (MOVIMENTO)" : "APAGADO (LIVRE)",
                  (agora - tempoMudanca));
  }

  // 4. Se o radar mandar dados pela UART, mostra em hexadecimal
  if (Serial1.available()) {
    Serial.print("📦 [UART DATA]: ");
    while (Serial1.available()) {
      uint8_t b = Serial1.read();
      Serial.printf("%02X ", b);
    }
    Serial.println();
  }
}
