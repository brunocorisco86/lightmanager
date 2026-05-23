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

void setup_time() {
  configTime(-3 * 3600, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("Sincronizando NTP...");
  
  int retries = 0;
  time_t now = time(nullptr);
  while (now < 8 * 3600 * 2 && retries < 20) {
    delay(1000);
    Serial.print(".");
    now = time(nullptr);
    retries++;
  }
  
  if (now >= 8 * 3600 * 2) {
    Serial.println("\nTempo sincronizado!");
  } else {
    Serial.println("\nFalha ao sincronizar tempo.");
  }
}

bool isNightTime() {
  time_t now = time(nullptr);
  if (now < 8 * 3600 * 2) return false; 
  struct tm *timeinfo = localtime(&now);
  int hour = timeinfo->tm_hour;
  Serial.print("Hora atual: ");
  Serial.println(hour);
  return (hour >= 18 || hour < 5);
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando a ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 30) {
    delay(1000);
    Serial.print(".");
    retries++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi conectado! IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFalha na conexão WiFi.");
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String messageTemp = "";
  for (int i = 0; i < length; i++) messageTemp += (char)payload[i];
  messageTemp.trim();
  
  Serial.print("MQTT Recebido [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(messageTemp);
  
  // Controle Frente (Canal 1)
  if (String(topic) == set_frente) {
    if (messageTemp == "ON") {
      if (digitalRead(pinFrente) == RELAY_OFF) {
        digitalWrite(pinFrente, RELAY_ON);
        client.publish(state_frente, "ON", true);
        Serial.println("-> Frente LIGADA (Active Low)");
      }
    } else if (messageTemp == "OFF") {
      if (digitalRead(pinFrente) == RELAY_ON) {
        digitalWrite(pinFrente, RELAY_OFF);
        client.publish(state_frente, "OFF", true);
        Serial.println("-> Frente DESLIGADA (Active Low)");
      }
    }
  }
  // Controle Fundos (Canal 2)
  else if (String(topic) == set_fundos) {
    if (messageTemp == "ON") {
      if (digitalRead(pinFundos) == RELAY_OFF) {
        digitalWrite(pinFundos, RELAY_ON);
        client.publish(state_fundos, "ON", true);
        Serial.println("-> Fundos LIGADO (Active Low)");
      }
    } else if (messageTemp == "OFF") {
      if (digitalRead(pinFundos) == RELAY_ON) {
        digitalWrite(pinFundos, RELAY_OFF);
        client.publish(state_fundos, "OFF", true);
        Serial.println("-> Fundos DESLIGADO (Active Low)");
      }
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Tentando conexão MQTT... ");
    String clientId = "WemosClient-" + String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("CONECTADO!");
      client.subscribe(set_frente);
      client.subscribe(set_fundos);
      Serial.println("Tópicos assinados.");
    } else {
      Serial.print("FALHOU, rc=");
      Serial.print(client.state());
      Serial.println(" tentando novamente em 5s");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  // No Active Low, HIGH desliga o relé.
  digitalWrite(pinFrente, RELAY_OFF);
  digitalWrite(pinFundos, RELAY_OFF);
  pinMode(pinFrente, OUTPUT);
  pinMode(pinFundos, OUTPUT);
  
  setup_wifi();
  
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  
  if (WiFi.status() == WL_CONNECTED) {
    setup_time();
    if (isNightTime()) {
      Serial.println("Modo noturno detectado. Ligando luzes.");
      digitalWrite(pinFrente, RELAY_ON);
      digitalWrite(pinFundos, RELAY_ON);
      
      if (client.connect("WemosInit", mqtt_user, mqtt_password)) {
        client.publish(state_frente, "ON", true);
        client.publish(state_fundos, "ON", true);
        client.subscribe(set_frente);
        client.subscribe(set_fundos);
      }
    }
  }
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) setup_wifi();
  if (WiFi.status() == WL_CONNECTED && !client.connected()) reconnect();
  if (client.connected()) client.loop();
  
  unsigned long now = millis();
  if (now - lastMsg > 60000) {
    lastMsg = now;
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
