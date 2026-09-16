#include <WiFi.h>
#include <PubSubClient.h>

// ==========================================
// Configurações de Hardware e Pinos
// ==========================================
// ESP32-C3 SuperMini + Radar LD2420
const int PIN_RADAR_OUT = 2;   // Pino OUT do LD2420 (Digital HIGH = Presença)
const int PIN_RADAR_RX  = 20;  // RX do ESP32-C3 conectado ao TX do LD2420
const int PIN_RADAR_TX  = 21;  // TX do ESP32-C3 conectado ao RX do LD2420
const int PIN_LED_BUILDIN = 8; // LED onboard do ESP32-C3 SuperMini (Active LOW)

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
// Constantes de Temporização
// ==========================================
// 2 minutos = 120.000 ms
const unsigned long LIGHT_TIMEOUT_MS = 120000;
const unsigned long STATUS_INTERVAL_MS = 30000; // Heartbeat a cada 30s

// ==========================================
// Objetos e Variáveis Globais
// ==========================================
WiFiClient espClient;
PubSubClient client(espClient);

bool presenceActive = false;
bool lightIsOn = false;
unsigned long lastMotionTime = 0;
unsigned long lastPulseHighTime = 0;
unsigned long lastStatusMsg = 0;
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

  // Sincroniza estado real do muro caso receba atualização do Wemos
  if (String(topic) == TOPIC_MURO_STATE) {
    lightIsOn = (msg == "ON");
    Serial.printf("[MQTT] Estado do Muro atualizado: %s\n", msg.c_str());
  }
}

boolean reconnect_mqtt() {
  Serial.print("Tentando conexao MQTT... ");
  String clientId = "ESP32C3-Radar-" + String(random(0xffff), HEX);

  if (client.connect(clientId.c_str(), mqtt_user, mqtt_password, TOPIC_RADAR_STATUS, 1, true, "{\"status\":\"offline\"}")) {
    Serial.println("CONECTADO!");
    client.subscribe(TOPIC_MURO_STATE);
    
    // Publica status de online
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

  unsigned long remainingSec = 0;
  if (lightIsOn && lastMotionTime > 0) {
    unsigned long elapsed = millis() - lastMotionTime;
    if (elapsed < LIGHT_TIMEOUT_MS) {
      remainingSec = (LIGHT_TIMEOUT_MS - elapsed) / 1000;
    }
  }

  String payload = "{";
  payload += "\"status\":\"online\",";
  payload += "\"presence\":" + String(presenceActive ? "true" : "false") + ",";
  payload += "\"light_muro\":" + String(lightIsOn ? "true" : "false") + ",";
  payload += "\"timeout_remaining_s\":" + String(remainingSec) + ",";
  payload += "\"motion_count\":" + String(motionCounter) + ",";
  payload += "\"rssi\":" + String(WiFi.RSSI()) + ",";
  payload += "\"ip\":\"" + WiFi.localIP().toString() + "\"";
  payload += "}";

  client.publish(TOPIC_RADAR_STATUS, payload.c_str(), false);
}

void setup() {
  // Inicializa porta USB CDC nativa para terminal serial
  Serial.begin(115200);
  delay(1500); // Aguarda estabilização do CDC

  Serial.println("\n==================================================");
  Serial.println("🚀 ESP32-C3 SuperMini - PoC Radar LD2420 + Light");
  Serial.println("==================================================");

  // Configuração dos Pinos
  pinMode(PIN_RADAR_OUT, INPUT_PULLDOWN);
  pinMode(PIN_LED_BUILDIN, OUTPUT);
  digitalWrite(PIN_LED_BUILDIN, HIGH); // Apagado (active LOW)

  // Inicializa UART1 com o radar LD2420 para telemetria opcional
  Serial1.begin(115200, SERIAL_8N1, PIN_RADAR_RX, PIN_RADAR_TX);
  Serial.println("📡 Serial1 do Radar LD2420 inicializada em 115200 baud.");

  // Configuração de Rede
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqtt_callback);

  Serial.println("Pronto! Aguardando detecção de presença...\n");
}

void loop() {
  unsigned long now = millis();

  // 1. Manutenção de Conexão Wi-Fi e MQTT
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

  // 2. Leitura do Sensor Radar LD2420 (Pino OUT)
  int radarReading = digitalRead(PIN_RADAR_OUT);
  bool currentPresence = (radarReading == HIGH);

  // 3. Processa dados da Serial1 do LD2420 se disponíveis (log/debug)
  while (Serial1.available()) {
    char c = (char)Serial1.read();
    // Eco opcional de bytes ou pacotes do radar
  }

  // 4. Lógica de Detecção de Movimento e Acionamento da Luz do Muro
  if (currentPresence) {
    lastPulseHighTime = now;
    lastMotionTime = now;               // Retrigger do temporizador de 2 minutos
    digitalWrite(PIN_LED_BUILDIN, LOW); // Liga LED indicador onboard

    if (!presenceActive) {
      presenceActive = true;
      motionCounter++;
      Serial.printf("🏃 [PRESENÇA DETECTADA] Pulso HIGH no GPIO 2! (Contagem: %lu)\n", motionCounter);

      if (client.connected()) {
        client.publish(TOPIC_RADAR_PRESENCE, "ON", true);
        
        // Se a luz estiver apagada, envia comando para ligar
        if (!lightIsOn) {
          Serial.println("💡 Enviando comando MQTT: LIGAR Luz do Muro (home/outdoor/muro/set -> ON)");
          client.publish(TOPIC_MURO_SET, "ON", false);
          lightIsOn = true;
        }
      }
    }
  } else {
    // Histerese de 2000ms: só desativa presença se ficar LOW continuamente por 2 segundos
    if (presenceActive && (now - lastPulseHighTime >= 2000)) {
      presenceActive = false;
      digitalWrite(PIN_LED_BUILDIN, HIGH); // Apaga LED indicador onboard
      Serial.println("🚶 [PRESENÇA CESSADA] Sem movimento por 2s. Temporizador de 2 min em contagem...");
      if (client.connected()) {
        client.publish(TOPIC_RADAR_PRESENCE, "OFF", true);
      }
    }
  }

  // 5. Verificação do Temporizador de 2 minutos (120s)
  if (lightIsOn && lastMotionTime > 0) {
    if (now - lastMotionTime >= LIGHT_TIMEOUT_MS) {
      Serial.println("⏱️ [TEMPORIZADOR EXPIRADO] 2 minutos sem presença. Desligando Luz do Muro...");
      if (client.connected()) {
        client.publish(TOPIC_MURO_SET, "OFF", false);
      }
      lightIsOn = false;
      lastMotionTime = 0;
    }
  }

  // 6. Telemetria periódica
  if (now - lastStatusMsg > STATUS_INTERVAL_MS) {
    lastStatusMsg = now;
    publish_telemetry();
  }
}
