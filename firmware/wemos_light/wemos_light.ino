#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <time.h>

// Configurações de Wi-Fi
const char* ssid = "quarto";
const char* password = "veracruz";

// Configurações de MQTT
const char* mqtt_server = "192.168.1.7";
const int mqtt_port = 1883;
const char* mqtt_user = "bruno";
const char* mqtt_password = "blurbang";

// Lógica Invertida (Active Low)
#define RELAY_ON LOW
#define RELAY_OFF HIGH

// Definições de Tópicos e Pinos
const char* set_frente = "home/outdoor/frente/set";
const char* state_frente = "home/outdoor/frente/state";
const int pinFrente = D1; 

const char* set_fundos = "home/outdoor/fundos/set";
const char* state_fundos = "home/outdoor/fundos/state";
const int pinFundos = D2;

const char* status_topic = "home/outdoor/status";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;
unsigned long lastReconnectAttempt = 0;
unsigned long lastHealthCheck = 0;

void setup_time() {
  configTime(-3 * 3600, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("Sincronizando NTP...");
  
  int retries = 0;
  time_t now = time(nullptr);
  while (now < 8 * 3600 * 2 && retries < 15) {
    delay(1000);
    Serial.print(".");
    now = time(nullptr);
    retries++;
  }
  
  if (now >= 8 * 3600 * 2) {
    Serial.println("\nTempo sincronizado!");
  } else {
    Serial.println("\nNTP pendente (continuara tentando no loop).");
  }
}

bool isNightTime() {
  time_t now = time(nullptr);
  if (now < 8 * 3600 * 2) return false; 
  struct tm *timeinfo = localtime(&now);
  return (timeinfo->tm_hour >= 18 || timeinfo->tm_hour < 5);
}

void setup_wifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  
  Serial.print("\nConectando a ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 20) {
    delay(500);
    Serial.print(".");
    retries++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi OK! IP: " + WiFi.localIP().toString());
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String messageTemp = "";
  for (int i = 0; i < length; i++) messageTemp += (char)payload[i];
  messageTemp.trim();
  
  if (String(topic) == set_frente) {
    if (messageTemp == "ON" && digitalRead(pinFrente) == RELAY_OFF) {
      digitalWrite(pinFrente, RELAY_ON);
      client.publish(state_frente, "ON", true);
    } else if (messageTemp == "OFF" && digitalRead(pinFrente) == RELAY_ON) {
      digitalWrite(pinFrente, RELAY_OFF);
      client.publish(state_frente, "OFF", true);
    }
  }
  else if (String(topic) == set_fundos) {
    if (messageTemp == "ON" && digitalRead(pinFundos) == RELAY_OFF) {
      digitalWrite(pinFundos, RELAY_ON);
      client.publish(state_fundos, "ON", true);
    } else if (messageTemp == "OFF" && digitalRead(pinFundos) == RELAY_ON) {
      digitalWrite(pinFundos, RELAY_OFF);
      client.publish(state_fundos, "OFF", true);
    }
  }
}

boolean reconnect() {
  Serial.print("Tentando MQTT... ");
  String clientId = "WemosLight-" + String(random(0xffff), HEX);
  
  if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
    Serial.println("CONECTADO!");
    client.subscribe(set_frente);
    client.subscribe(set_fundos);
    // Publica estado atual ao reconectar para sincronizar site
    client.publish(state_frente, (digitalRead(pinFrente) == RELAY_ON ? "ON" : "OFF"), true);
    client.publish(state_fundos, (digitalRead(pinFundos) == RELAY_ON ? "ON" : "OFF"), true);
  } else {
    Serial.print("Falhou, rc=");
    Serial.println(client.state());
  }
  return client.connected();
}

void setup() {
  Serial.begin(115200);
  
  digitalWrite(pinFrente, RELAY_OFF);
  digitalWrite(pinFundos, RELAY_OFF);
  pinMode(pinFrente, OUTPUT);
  pinMode(pinFundos, OUTPUT);
  
  setup_wifi();
  
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  
  if (WiFi.status() == WL_CONNECTED) {
    setup_time();
    // Se for noite no boot, liga as luzes imediatamente mesmo sem MQTT
    if (isNightTime()) {
      digitalWrite(pinFrente, RELAY_ON);
      digitalWrite(pinFundos, RELAY_ON);
    }
  }
}

void loop() {
  unsigned long now = millis();

  // 1. Mantém Wi-Fi vivo
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  // 2. Política de Verificação de Conexão (Broker)
  if (WiFi.status() == WL_CONNECTED) {
    
    // Check de Saúde a cada 5 minutos (Força reconexão se houver dúvida)
    if (now - lastHealthCheck > 300000) {
      lastHealthCheck = now;
      Serial.println("\n[HealthCheck] Verificando conexao com Broker...");
      if (!client.connected()) {
        Serial.println("[HealthCheck] Broker offline. Reiniciando tentativa...");
      } else {
        // Ping de teste para o Broker
        if (!client.publish("home/outdoor/heartbeat", "check")) {
          Serial.println("[HealthCheck] Falha no ping. Forcando reconexao...");
          client.disconnect();
        } else {
          Serial.println("[HealthCheck] Broker OK.");
        }
      }
    }

    // Tentativa não-bloqueante a cada 5 segundos se estiver desconectado
    if (!client.connected()) {
      if (now - lastReconnectAttempt > 5000) {
        lastReconnectAttempt = now;
        if (reconnect()) {
          lastReconnectAttempt = 0;
        }
      }
    } else {
      client.loop();
    }
  }

  // 3. Heartbeat e Status (a cada 60s)
  if (now - lastMsg > 60000) {
    lastMsg = now;
    
    // Fallback de Segurança: Se o NTP sincronizou e virou dia, garante desligamento
    if (WiFi.status() == WL_CONNECTED && !isNightTime() && time(nullptr) > 1000000) {
       if (digitalRead(pinFrente) == RELAY_ON) digitalWrite(pinFrente, RELAY_OFF);
       if (digitalRead(pinFundos) == RELAY_ON) digitalWrite(pinFundos, RELAY_OFF);
    }

    if (client.connected()) {
      String q = String((char)34);
      String payload = "{";
      payload += q + "status" + q + ":" + q + "online" + q + ",";
      payload += q + "frente" + q + ":" + q + (digitalRead(pinFrente) == RELAY_ON ? "ON" : "OFF") + q + ",";
      payload += q + "fundos" + q + ":" + q + (digitalRead(pinFundos) == RELAY_ON ? "ON" : "OFF") + q + ",";
      payload += q + "rssi" + q + ":" + String(WiFi.RSSI()) + ",";
      payload += q + "ip" + q + ":" + q + WiFi.localIP().toString() + q;
      payload += "}";
      client.publish(status_topic, payload.c_str());
    }
  }
}
