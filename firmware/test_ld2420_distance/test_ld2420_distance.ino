#include <Arduino.h>
#include "LD2420.h"

// Pinos de Comunicação Serial com o LD2420 no ESP32-C3 SuperMini
const int PIN_RADAR_RX = 20; // Conectado ao OT1 (Pino 3) ou OT2 (Pino 5)
const int PIN_RADAR_TX = 21; // Conectado ao RX (Pino 4 do sensor)
const int PIN_LED      = 8;  // LED onboard do ESP32-C3 SuperMini (Active LOW)

LD2420 radar;
unsigned long ultimoAviso = 0;
unsigned long ultimoStatus = 0;

void onDetection(int distance) {
  // Disparado quando detecta alvo na faixa configurada
  digitalWrite(PIN_LED, LOW); // Acende LED onboard
  Serial.printf("✅ [ALVO DETECTADO] Distância: %d cm | Dentro do limite!\n", distance);
  ultimoAviso = millis();
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, HIGH); // Apagado

  // Inicializa Hardware Serial1 nos pinos 20 e 21
  Serial1.begin(115200, SERIAL_8N1, PIN_RADAR_RX, PIN_RADAR_TX);

  Serial.println("\n=======================================================");
  Serial.println("🎯 TESTE COM MEDIÇÃO REAL DE DISTÂNCIA - LD2420");
  Serial.println("  ESP32 GPIO 20 (RX) -> OT1 / OT2 do Sensor");
  Serial.println("  ESP32 GPIO 21 (TX) -> RX do Sensor");
  Serial.println("=======================================================\n");

  if (radar.begin(Serial1)) {
    // Configura a faixa de distância (ex: 30 cm a 250 cm)
    radar.setDistanceRange(30, 250);
    radar.setUpdateInterval(50); // 50ms
    radar.onDetection(onDetection);

    Serial.println("📏 Faixa de detecção configurada: 30 cm a 250 cm");
    Serial.println("Pronto! Passe a mão ou caminhe na frente do sensor.\n");
  } else {
    Serial.println("⚠️ Falha ao inicializar comunicação serial com o sensor.");
    Serial.println("Tentando continuar a leitura...");
  }
}

void loop() {
  radar.update();

  unsigned long agora = millis();

  // Apaga LED onboard após 500ms sem detecção
  if (agora - ultimoAviso > 500) {
    digitalWrite(PIN_LED, HIGH);
  }

  // Linha de status calmo a cada 1000 ms se não houver detecção
  if (agora - ultimoStatus >= 1000) {
    ultimoStatus = agora;
    if (agora - ultimoAviso > 1000) {
      Serial.printf("⚪ [SEM ALVO NO RAIO DE 2.5M] | LED: APAGADO | Distância: %d cm\n", radar.getDistance());
    }
  }

  // Mostra qualquer byte recebido na Serial1 se houver
  if (Serial1.available()) {
    while (Serial1.available()) {
      Serial1.read();
    }
  }

  delay(10);
}
