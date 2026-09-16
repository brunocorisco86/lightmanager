#include <WiFi.h>
#include <PubSubClient.h>
#include "LD2420.h"

// ==========================================
// Configurações de Hardware e Pinos
// ==========================================
// ESP32-C3 SuperMini + Radar LD2420 via UART
const int PIN_RADAR_RX    = 20; // RX do ESP32-C3 ligado ao OT1 (Pino 3) do LD2420
const int PIN_RADAR_TX    = 21; // TX do ESP32-C3 ligado ao RX (Pino 4) do LD2420
const int PIN_LED_BUILDIN = 8;  // LED onboard do ESP32-C3 SuperMini (Active LOW)

// ==========================================
// Configurações de Rede e MQTT
// ==========================================
const char* ssid          = "ZN-BRUNO_CONTER";
const char* password      = "veracruz";
const char* mqtt_server   = "192.168.1.7";
const int   mqtt_port     = 1883;
const char* mqtt_user     = "bruno";
const char* mqtt_password = "blurbang";

// Tópicos MQTT
const char* TOPIC_MURO_SET       = "home/outdoor/muro/set";
const char* TOPIC_MURO_STATE     = "home/outdoor/muro/state";
const char* TOPIC_RADAR_PRESENCE = "home/outdoor/radar/presence";
const char* TOPIC_RADAR_STATUS   = "home/outdoor/radar/status";
const char* TOPIC_RADAR_LOG      = "home/outdoor/radar/log";

// ==========================================
// Constantes de Temporização e Faixa de Radar
// ==========================================
const unsigned long LIGHT_TIMEOUT_MS   = 120000; // 2 minutos
const unsigned long STATUS_INTERVAL_MS = 10000;  // Telemetria a cada 10s
const int RADAR_MIN_DIST_CM            = 30;     // Mínimo: 30 cm
const int RADAR_MAX_DIST_CM            = 250;    // Máximo: 250 cm (2,5m) - ignora além disso!
const unsigned long PRESENCE_HOLD_MS   = 1500;   // Mantém ON por 1.5s após última detecção

// Trava de Segurança: não aciona relés durante teste de baseline na janela
const bool ENABLE_RELAY_TRIGGER = false; 

// ==========================================
// Objetos e Variáveis Globais
// ==========================================
WiFiClient espClient;
PubSubClient client(espClient);
LD2420 radar;

bool presenceActive = false;
bool lightIsOn = false;
int currentDistanceCm = 0;
unsigned long lastDetectionTime = 0;
unsigned long lastStatusMsg = 0;
unsigned long lastSerialPrint = 0;
unsigned long motionCounter = 0;
unsigned long lastReconnectAttempt = 0;

void setup_wifi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.println();
  Serial.print("Conectando ao Wi-Fi: ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 25) {
    delay(500);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ Wi-Fi Conectado!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("RSSI: ");
    Serial.println(WiFi.RSSI());
  } else {
    Serial.println("\n⚠️ Falha ao conectar ao Wi-Fi. Tentará novamente no loop.");
  }
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  msg.trim();

  if (String(topic) == TOPIC_MURO_STATE) {
    lightIsOn = (msg == "ON");
    Serial.printf("[MQTT] Estado do Muro atualizado: %s\n", msg.c_str());
  }
}

boolean reconnect_mqtt() {
  Serial.print("Tentando conexão MQTT... ");
  String clientId = "ESP32C3-Radar-" + String(random(0xffff), HEX);

  if (client.connect(clientId.c_str(), mqtt_user, mqtt_password, TOPIC_RADAR_STATUS, 1, true, "{\"status\":\"offline\"}")) {
    Serial.println("CONECTADO!");
    client.subscribe(TOPIC_MURO_STATE);
    
    // Publica status de online e estado atual da presença
    client.publish(TOPIC_RADAR_STATUS, "{\"status\":\"online\"}", true);
    client.publish(TOPIC_RADAR_PRESENCE, presenceActive ? "ON" : "OFF", true);
    return true;
  } else {
    Serial.print("Falha rc=");
    Serial.println(client.state());
    return false;
  }
}

void publish_telemetry() {
  if (!client.connected()) return;

  String payload = "{";
  payload += "\"status\":\"online\",";
  payload += "\"presence\":" + String(presenceActive ? "true" : "false") + ",";
  payload += "\"distance_cm\":" + String(currentDistanceCm) + ",";
  payload += "\"light_muro\":" + String(lightIsOn ? "true" : "false") + ",";
  payload += "\"motion_count\":" + String(motionCounter) + ",";
  payload += "\"rssi\":" + String(WiFi.RSSI()) + ",";
  payload += "\"ip\":\"" + WiFi.localIP().toString() + "\"";
  payload += "}";

  client.publish(TOPIC_RADAR_STATUS, payload.c_str(), false);
}

void onDetection(int distance) {
  unsigned long now = millis();
  currentDistanceCm = distance;
  lastDetectionTime = now;
  digitalWrite(PIN_LED_BUILDIN, LOW); // Acende LED onboard (Active LOW)

  if (!presenceActive) {
    presenceActive = true;
    motionCounter++;
    Serial.printf("\n🏃 [PRESENÇA ATIVA] Alvo detectado a %d cm! (Total: %lu)\n", distance, motionCounter);

    if (client.connected()) {
      client.publish(TOPIC_RADAR_PRESENCE, "ON", true);
      publish_telemetry();
      
      if (ENABLE_RELAY_TRIGGER && !lightIsOn) {
        Serial.println("💡 Enviando comando MQTT: LIGAR Luz do Muro");
        client.publish(TOPIC_MURO_SET, "ON", false);
        lightIsOn = true;
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  Serial.println("\n==================================================");
  Serial.println("🚀 ESP32-C3 SuperMini - Radar LD2420 UART + MQTT");
  Serial.println("   OT1 (Pino 3) -> GPIO 20 (Serial1 RX)");
  Serial.println("   RX  (Pino 4) -> GPIO 21 (Serial1 TX)");
  Serial.println("==================================================");

  pinMode(PIN_LED_BUILDIN, OUTPUT);
  digitalWrite(PIN_LED_BUILDIN, HIGH); // Apagado

  // Inicializa Hardware Serial1 nos pinos 20 e 21
  Serial1.begin(115200, SERIAL_8N1, PIN_RADAR_RX, PIN_RADAR_TX);

  // Inicializa o Radar LD2420
  if (radar.begin(Serial1)) {
    radar.setDistanceRange(RADAR_MIN_DIST_CM, RADAR_MAX_DIST_CM);
    radar.setUpdateInterval(50); // 20Hz
    radar.onDetection(onDetection);
    Serial.printf("📏 Radar LD2420 OK! Faixa: %d cm a %d cm\n", RADAR_MIN_DIST_CM, RADAR_MAX_DIST_CM);
  } else {
    Serial.println("⚠️ Falha na inicializacao do radar via Serial1. Verifique as ligacoes.");
  }

  // Inicializa Rede
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqtt_callback);

  Serial.println("Pronto! Aguardando operacao...\n");
}

void loop() {
  unsigned long now = millis();

  // 1. Manutenção de Rede Wi-Fi e MQTT
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  } else {
    if (!client.connected()) {
      if (now - lastReconnectAttempt > 5000) {
        lastReconnectAttempt = now;
        if (reconnect_mqtt()) {
          lastReconnectAttempt = 0;
        }
      }
    } else {
      client.loop();
    }
  }

  // 2. Atualização da Leitura do Radar
  radar.update();

  // 3. Verificação de Encerramento de Presença (Hold de 1.5 segundos)
  if (presenceActive && (now - lastDetectionTime > PRESENCE_HOLD_MS)) {
    presenceActive = false;
    currentDistanceCm = 0;
    digitalWrite(PIN_LED_BUILDIN, HIGH); // Apaga LED onboard
    Serial.println("⚪ [PRESENÇA CESSADA] Sem alvos na faixa. Estado: OFF");

    if (client.connected()) {
      client.publish(TOPIC_RADAR_PRESENCE, "OFF", true);
      publish_telemetry();
    }
  }

  // 4. Log Serial Periódico e Calmo (a cada 1 segundo)
  if (now - lastSerialPrint >= 1000) {
    lastSerialPrint = now;
    Serial.printf("[STATUS] Presenca: %s | Distancia: %d cm | MQTT: %s | WiFi: %d dBm\n",
                  presenceActive ? "ON (ATIVA)" : "OFF (REPOUSO)",
                  currentDistanceCm,
                  client.connected() ? "CONECTADO" : "DESCONECTADO",
                  WiFi.RSSI());
  }

  // 5. Telemetria MQTT Periódica (a cada 10 segundos)
  if (now - lastStatusMsg > STATUS_INTERVAL_MS) {
    lastStatusMsg = now;
    publish_telemetry();
  }
}
