#include <WiFi.h>
#include <PubSubClient.h>

// ==========================================
// Seleção da Versão do Firmware do LD2420
// ==========================================
// Caso 1 (Padrão/Mais Comum): FW <= 1.5.2 -> OT1 = Presença (GPIO 2), OT2 = TX UART (GPIO 20) @ 256.000 bps
// Caso 2: FW >= 1.5.3                     -> OT2 = Presença (GPIO 2), OT1 = TX UART (GPIO 20) @ 115.200 bps
#define LD2420_MODE_FW_LE_152
//#define LD2420_MODE_FW_GE_153

#ifdef LD2420_MODE_FW_LE_152
  const unsigned long RADAR_BAUD_RATE = 256000;
  const char* RADAR_FW_DESC = "Caso 1: FW <= 1.5.2 (OT1 = Presenca / OT2 = TX @ 256.000 bps)";
#else
  const unsigned long RADAR_BAUD_RATE = 115200;
  const char* RADAR_FW_DESC = "Caso 2: FW >= 1.5.3 (OT2 = Presenca / OT1 = TX @ 115.200 bps)";
#endif

// ==========================================
// Configurações de Hardware e Pinos
// ==========================================
// ESP32-C3 SuperMini + Radar LD2420
const int PIN_RADAR_OUT = 2;   // Pino de Presença Digital do LD2420 (OT1 no Caso 1 / OT2 no Caso 2)
const int PIN_RADAR_RX  = 20;  // RX do ESP32-C3 conectado ao TX do LD2420 (OT2 no Caso 1 / OT1 no Caso 2)
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
// Constantes de Filtro e Temporização
// ==========================================
// 2 minutos = 120.000 ms
const unsigned long LIGHT_TIMEOUT_MS = 120000;
const unsigned long STATUS_INTERVAL_MS = 30000; // Heartbeat a cada 30s
const unsigned long CONFIRMATION_TIME_MS = 300; // Mínimo HIGH contínuo para confirmar presença
const unsigned long RELEASE_TIME_MS = 3000;     // Mínimo LOW contínuo para encerrar presença

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

// Variáveis de Diagnóstico e Filtro
int lastRawPinState = -1;
unsigned long lastRawStateChangeTime = 0;
unsigned long lastStatusPrint = 0;
unsigned long highStartTime = 0;
unsigned long lowStartTime = 0;
const bool ENABLE_RELAY_TRIGGER = true; // Habilitado para acionar Muro e MQTT

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
  Serial.println("🚀 ESP32-C3 SuperMini - Diagnostico Radar LD2420");
  Serial.println("==================================================");

  // Configuração dos Pinos
  pinMode(PIN_RADAR_OUT, INPUT_PULLDOWN);
  pinMode(PIN_LED_BUILDIN, OUTPUT);
  digitalWrite(PIN_LED_BUILDIN, HIGH); // Apagado (active LOW)

  // Inicializa UART1 com o radar LD2420
  Serial1.begin(RADAR_BAUD_RATE, SERIAL_8N1, PIN_RADAR_RX, PIN_RADAR_TX);
  Serial.printf("📡 Serial1 do Radar LD2420 inicializada: %s\n", RADAR_FW_DESC);

  // Configuração de Rede
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqtt_callback);

  Serial.println("🔍 Monitor de Diagnostico Iniciado! Aguardando leituras...\n");
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

  // 2. Leitura e Diagnóstico Imediato do Pino OUT (GPIO 2)
  int radarReading = digitalRead(PIN_RADAR_OUT);
  
  if (radarReading != lastRawPinState) {
    unsigned long duration = (lastRawStateChangeTime > 0) ? (now - lastRawStateChangeTime) : 0;
    if (radarReading == HIGH) {
      highStartTime = now;
      Serial.printf("[TRANSITION] GPIO 2: LOW -> HIGH (ficou LOW por %lu ms)\n", duration);
    } else {
      lowStartTime = now;
      if (!presenceActive && (now - highStartTime < CONFIRMATION_TIME_MS)) {
        Serial.printf("🛡️ [GLITCH IGNORADO] Pulso HIGH durou apenas %lu ms (< %lu ms de confirmacao)\n", 
                      duration, CONFIRMATION_TIME_MS);
      } else {
        Serial.printf("[TRANSITION] GPIO 2: HIGH -> LOW (ficou HIGH por %lu ms)\n", duration);
      }
    }
    lastRawPinState = radarReading;
    lastRawStateChangeTime = now;
  }

  // Relatório periódico a cada 500ms
  if (now - lastStatusPrint >= 500) {
    lastStatusPrint = now;
    unsigned long stateDuration = now - lastRawStateChangeTime;
    Serial.printf("[STATUS] GPIO 2 RAW: %d | PresencaConfirmada: %s | DuracaoEstado: %lu ms | Movimentos: %lu\n",
                  radarReading,
                  presenceActive ? "SIM (ON)" : "NAO (OFF)",
                  stateDuration,
                  motionCounter);
  }

  // 3. Processa dados da Serial1 do LD2420 se disponíveis
  if (Serial1.available()) {
    String hexBuf = "";
    int count = 0;
    while (Serial1.available() && count < 32) {
      uint8_t b = Serial1.read();
      if (b < 0x10) hexBuf += "0";
      hexBuf += String(b, HEX);
      hexBuf += " ";
      count++;
    }
    hexBuf.toUpperCase();
    Serial.printf("[UART_RADAR] %d bytes: %s\n", count, hexBuf.c_str());
  }

  // 4. Lógica de Filtro Sustentado (> 300ms contínuo) e Histerese (> 3000ms contínuo)
  if (radarReading == HIGH) {
    if (!presenceActive) {
      // Verifica se permaneceu em HIGH por tempo suficiente
      if (now - highStartTime >= CONFIRMATION_TIME_MS) {
        presenceActive = true;
        motionCounter++;
        lastMotionTime = now;
        lastPulseHighTime = now;
        digitalWrite(PIN_LED_BUILDIN, LOW); // Liga LED indicador onboard
        Serial.printf("🏃 [PRESENÇA CONFIRMADA] GPIO 2 HIGH continuo por %lu ms! (Contagem: %lu)\n", 
                      (now - highStartTime), motionCounter);

        if (client.connected()) {
          client.publish(TOPIC_RADAR_PRESENCE, "ON", true);
          if (ENABLE_RELAY_TRIGGER && !lightIsOn) {
            Serial.println("💡 Enviando comando MQTT: LIGAR Luz do Muro");
            client.publish(TOPIC_MURO_SET, "ON", false);
            lightIsOn = true;
          }
        }
      }
    } else {
      lastMotionTime = now;
      lastPulseHighTime = now;
    }
  } else {
    // Está em LOW: só encerra após RELEASE_TIME_MS (3 segundos) contínuos em LOW
    if (presenceActive) {
      if (now - lowStartTime >= RELEASE_TIME_MS) {
        presenceActive = false;
        digitalWrite(PIN_LED_BUILDIN, HIGH); // Apaga LED indicador onboard
        Serial.printf("🚶 [PRESENÇA CESSADA] GPIO 2 LOW continuo por %lu ms.\n", RELEASE_TIME_MS);
        if (client.connected()) {
          client.publish(TOPIC_RADAR_PRESENCE, "OFF", true);
        }
      }
    }
  }

  // 5. Temporizador de 2 minutos (caso acionado)
  if (lightIsOn && lastMotionTime > 0) {
    if (now - lastMotionTime >= LIGHT_TIMEOUT_MS) {
      Serial.println("⏱️ [TEMPORIZADOR EXPIRADO] Desligando Luz do Muro...");
      if (client.connected() && ENABLE_RELAY_TRIGGER) {
        client.publish(TOPIC_MURO_SET, "OFF", false);
      }
      lightIsOn = false;
      lastMotionTime = 0;
    }
  }

  // 6. Telemetria periódica MQTT
  if (now - lastStatusMsg > STATUS_INTERVAL_MS) {
    lastStatusMsg = now;
    publish_telemetry();
  }
}
