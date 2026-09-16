// ==========================================================
// TESTE CALMO E ESTABILIZADO - ESP32-C3 + RADAR LD2420
// Taxa de 1 linha por segundo (1 Hz) | Sem flood de terminal
// ==========================================================

const int PIN_OT1 = 2; // Pino 3 (OT1) do LD2420 - Presença Digital
const int PIN_OT2 = 3; // Pino 5 (OT2) do LD2420 - TX Serial
const int PIN_LED = 8; // LED onboard do ESP32-C3 SuperMini (Active LOW)

int estadoConfirmadoOT1 = -1;
int estadoRawOT1 = -1;
unsigned long tempoInicioEstado = 0;
unsigned long ultimoPrint = 0;
unsigned long contadorMovimentos = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(PIN_OT1, INPUT_PULLDOWN);
  pinMode(PIN_OT2, INPUT_PULLDOWN);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, HIGH); // Apagado

  Serial.println("\n=======================================================");
  Serial.println("  🎯 MONITOR SERIAL ESTÁVEL E CALMO (1 SEGUNDO / LINHA)");
  Serial.println("  OT1 (Pino 3 do sensor) -> GPIO 2 (Presença)");
  Serial.println("  OT2 (Pino 5 do sensor) -> GPIO 3 (TX Serial)");
  Serial.println("  LED Onboard (GPIO 8)   -> Espelho visual instantâneo");
  Serial.println("=======================================================\n");
}

void loop() {
  unsigned long agora = millis();
  int rawOT1 = digitalRead(PIN_OT1);
  int rawOT2 = digitalRead(PIN_OT2);

  // Espelho instantâneo no LED onboard (sem atraso na placa)
  if (rawOT1 == HIGH) {
    digitalWrite(PIN_LED, LOW); // Acende LED onboard
  } else {
    digitalWrite(PIN_LED, HIGH); // Apaga LED onboard
  }

  // Filtro de confirmação anti-spam: precisa durar pelo menos 200 ms
  if (rawOT1 != estadoRawOT1) {
    estadoRawOT1 = rawOT1;
    tempoInicioEstado = agora;
  } else {
    if (rawOT1 != estadoConfirmadoOT1 && (agora - tempoInicioEstado >= 200)) {
      estadoConfirmadoOT1 = rawOT1;
      if (estadoConfirmadoOT1 == HIGH) {
        contadorMovimentos++;
        Serial.printf("\n⚡ >>> [MOVIMENTO DETECTADO] Alvo ativo! (Total: %lu) <<<\n\n", contadorMovimentos);
      } else {
        Serial.println("\n⚪ >>> [FIM DO MOVIMENTO] Sensor voltou ao repouso. <<<\n");
      }
    }
  }

  // Linha fixa e calma a cada 1000 ms (1 segundo exato)
  if (agora - ultimoPrint >= 1000) {
    ultimoPrint = agora;

    if (rawOT1 == HIGH) {
      Serial.printf("🏃 [PRESENÇA ATIVA] | OT1 (GPIO 2): 1 (3.3V) | LED: ACESO 💡 | Movimentos: %lu\n", contadorMovimentos);
    } else {
      Serial.printf("⚪ [LIVRE/REPOUSO]  | OT1 (GPIO 2): 0 (0.0V) | LED: APAGADO  | Movimentos: %lu\n", contadorMovimentos);
    }
  }
}
