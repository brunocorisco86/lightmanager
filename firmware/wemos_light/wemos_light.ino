#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Configurações de Wi-Fi
const char* ssid = "SEU_SSID";
const char* password = "SUA_SENHA_WIFI";

// Configurações de MQTT
const char* mqtt_server = "IP_DO_RASPBERRY";
const int mqtt_port = 1883;

// ATENÇÃO: Ajuste o tópico base para cada Wemos (Ex: home/outdoor/frente ou home/outdoor/fundos)
const char* base_topic = "home/outdoor/frente"; 
String topic_set = String(base_topic) + "/set";
String topic_state = String(base_topic) + "/state";

const int relayPin = D1; // Pino do relé

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
  Serial.println("\nWiFi conectado. IP: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  String messageTemp;
  for (int i = 0; i < length; i++) messageTemp += (char)payload[i];
  
  if (String(topic) == topic_set) {
    if (messageTemp == "ON") {
      digitalWrite(relayPin, HIGH); // Ajuste HIGH/LOW conforme modulo rele
      client.publish(topic_state.c_str(), "ON");
      Serial.println("Luz LIGADA");
    } else if (messageTemp == "OFF") {
      digitalWrite(relayPin, LOW);
      client.publish(topic_state.c_str(), "OFF");
      Serial.println("Luz DESLIGADA");
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Tentando MQTT...");
    // Nome unico do client (pode concatenar com um ID se houver varios)
    String clientId = "WemosClient-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("Conectado");
      client.subscribe(topic_set.c_str());
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
  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, LOW); 
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
    // Opcional: Publicar um ping para monitoramento (ex: online)
    client.publish((String(base_topic) + "/status").c_str(), "online");
  }
}
