#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Configurações de Wi-Fi
const char* ssid = "quarto";
const char* password = "veracruz";

// Configurações de MQTT
const char* mqtt_server = "192.168.1.7";
const int mqtt_port = 1883;
const char* mqtt_user = "bruno";
const char* mqtt_password = "blurbang";

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

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando a ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("
WiFi conectado. IP: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  String messageTemp;
  for (int i = 0; i < length; i++) messageTemp += (char)payload[i];
  
  // Controle Frente (Canal 1)
  if (String(topic) == set_frente) {
    if (messageTemp == "ON") {
      digitalWrite(pinFrente, HIGH);
      client.publish(state_frente, "ON");
      Serial.println("Frente LIGADA");
    } else if (messageTemp == "OFF") {
      digitalWrite(pinFrente, LOW);
      client.publish(state_frente, "OFF");
      Serial.println("Frente DESLIGADA");
    }
  }
  
  // Controle Fundos (Canal 2)
  else if (String(topic) == set_fundos) {
    if (messageTemp == "ON") {
      digitalWrite(pinFundos, HIGH);
      client.publish(state_fundos, "ON");
      Serial.println("Fundos LIGADO");
    } else if (messageTemp == "OFF") {
      digitalWrite(pinFundos, LOW);
      client.publish(state_fundos, "OFF");
      Serial.println("Fundos DESLIGADO");
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Tentando MQTT...");
    String clientId = "WemosClient-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("Conectado");
      client.subscribe(set_frente);
      client.subscribe(set_fundos);
    } else {
      Serial.print("Falhou, rc=");
      Serial.print(client.state());
      Serial.println(" tentando novamente em 5s");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(pinFrente, OUTPUT);
  digitalWrite(pinFrente, LOW); 
  pinMode(pinFundos, OUTPUT);
  digitalWrite(pinFundos, LOW); 
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();
  
  // Keep Alive / Heartbeat (Envia status a cada 60 segundos)
  unsigned long now = millis();
  if (now - lastMsg > 60000) {
    lastMsg = now;
    
    int rssi = WiFi.RSSI();
    String quality;
    if (rssi > -50) quality = "Excellent";
    else if (rssi > -60) quality = "Good";
    else if (rssi > -70) quality = "Fair";
    else quality = "Poor";

    String payload = "{";
    payload += ""status": "online",";
    payload += ""frente": "" + String(digitalRead(pinFrente) ? "ON" : "OFF") + "",";
    payload += ""fundos": "" + String(digitalRead(pinFundos) ? "ON" : "OFF") + "",";
    payload += ""rssi": " + String(rssi) + ",";
    payload += ""ip": "" + WiFi.localIP().toString() + """;
    payload += "}";
    
    client.publish(status_topic, payload.c_str());
  }
}
