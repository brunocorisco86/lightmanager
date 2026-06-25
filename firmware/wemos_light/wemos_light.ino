#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <time.h>
#include <sys/time.h>

// Configurações de Wi-Fi
const char* ssid = "ZN-BRUNO_CONTER";
const char* password = "veracruz";

// Configuração de IP Estático
IPAddress local_IP(192, 168, 1, 111);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(192, 168, 1, 7);  // unbound localserver
IPAddress secondaryDNS(1, 1, 1, 1);    // Cloudflare fallback

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

const char* system_reboot = "home/outdoor/system/reboot";
const char* status_topic = "home/outdoor/status";
const char* fallback_on_topic = "home/outdoor/fallback/on";
const char* fallback_off_topic = "home/outdoor/fallback/off";
const char* time_topic = "home/outdoor/time";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;
unsigned long lastReconnectAttempt = 0;
unsigned long lastHealthCheck = 0;
unsigned long lastMqttConnected = 0;
unsigned long lastWiFiConnected = 0;

int fallback_on_hour = 18;
int fallback_on_minute = 15;
int fallback_off_hour = 7;
int fallback_off_minute = 30;
bool has_fallback_times = false;

bool isFallbackNightTime(int cur_hour, int cur_min) {
  if (cur_hour > fallback_on_hour || (cur_hour == fallback_on_hour && cur_min >= fallback_on_minute)) {
    return true;
  }
  if (cur_hour < fallback_off_hour || (cur_hour == fallback_off_hour && cur_min < fallback_off_minute)) {
    return true;
  }
  return false;
}

void setup_time() {
  configTime("<-03>3", nullptr);
  Serial.println("Timezone GMT-3 configurado. Sincronizacao de tempo exclusiva via MQTT.");
}

bool isNightTime() {
  time_t now = time(nullptr);
  if (now < 8 * 3600 * 2) return false;
  struct tm* timeinfo = localtime(&now);
  if (has_fallback_times) {
    return isFallbackNightTime(timeinfo->tm_hour, timeinfo->tm_min);
  }
  return (timeinfo->tm_hour >= 18 || timeinfo->tm_hour < 8);
}

void setup_wifi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("\nConfigurando IP Estatico: ");
  Serial.println(local_IP);

  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
    Serial.println("Falha ao configurar IP Estatico");
  }

  Serial.print("Conectando a ");
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
    if (messageTemp == "ON") {
      digitalWrite(pinFrente, RELAY_ON);
      client.publish(state_frente, "ON", true);
    } else if (messageTemp == "OFF") {
      digitalWrite(pinFrente, RELAY_OFF);
      client.publish(state_frente, "OFF", true);
    }
  } else if (String(topic) == set_fundos) {
    if (messageTemp == "ON") {
      digitalWrite(pinFundos, RELAY_ON);
      client.publish(state_fundos, "ON", true);
    } else if (messageTemp == "OFF") {
      digitalWrite(pinFundos, RELAY_OFF);
      client.publish(state_fundos, "OFF", true);
    }
  } else if (String(topic) == system_reboot) {
    if (messageTemp == "REBOOT") {
      Serial.println("Comando REBOOT recebido via MQTT!");
      delay(500);
      ESP.restart();
    }
  } else if (String(topic) == fallback_on_topic) {
    if (length >= 5) {
      int h = messageTemp.substring(0, 2).toInt();
      int m = messageTemp.substring(3, 5).toInt();
      if (h >= 0 && h < 24 && m >= 0 && m < 60) {
        fallback_on_hour = h;
        fallback_on_minute = m;
        has_fallback_times = true;
        Serial.print("Fallback ON recebido: ");
        Serial.printf("%02d:%02d\n", fallback_on_hour, fallback_on_minute);
      }
    }
  } else if (String(topic) == fallback_off_topic) {
    if (length >= 5) {
      int h = messageTemp.substring(0, 2).toInt();
      int m = messageTemp.substring(3, 5).toInt();
      if (h >= 0 && h < 24 && m >= 0 && m < 60) {
        fallback_off_hour = h;
        fallback_off_minute = m;
        has_fallback_times = true;
        Serial.print("Fallback OFF recebido: ");
        Serial.printf("%02d:%02d\n", fallback_off_hour, fallback_off_minute);
      }
    }
  } else if (String(topic) == time_topic) {
    long long epoch = messageTemp.toInt();
    if (epoch > 1700000000) { // Timestamp valido pos-2023
      struct timeval tv;
      tv.tv_sec = epoch;
      tv.tv_usec = 0;
      settimeofday(&tv, nullptr);
      Serial.print("Relogio local ajustado via MQTT para: ");
      Serial.println(epoch);
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
    client.subscribe(system_reboot);
    client.subscribe(fallback_on_topic);
    client.subscribe(fallback_off_topic);
    client.subscribe(time_topic);
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

  lastMqttConnected = millis();
  lastWiFiConnected = millis();
}

void loop() {
  unsigned long now = millis();

  // 1. Mantém Wi-Fi vivo
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  } else {
    lastWiFiConnected = now;
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
      lastMqttConnected = now;
      client.loop();
    }
  }

  // Watchdog local de Autocura (Se ficar sem WiFi ou MQTT por mais de 10 minutos, reinicia)
  if (now - lastWiFiConnected > 600000 || now - lastMqttConnected > 600000) {
    Serial.println("🚨 Watchdog local disparado! Sem conexao por mais de 10 min. Reiniciando...");
    delay(1000);
    ESP.restart();
  }

  // 3. Heartbeat e Status (a cada 60s)
  if (now - lastMsg > 60000) {
    lastMsg = now;

    // Fallback de Segurança: Se o NTP sincronizou e virou dia, garante desligamento (apenas se desconectado do Broker)
    if (WiFi.status() == WL_CONNECTED && !client.connected() && !isNightTime() && time(nullptr) > 1000000) {
      if (digitalRead(pinFrente) == RELAY_ON) {
        digitalWrite(pinFrente, RELAY_OFF);
        if (client.connected()) {
          client.publish(state_frente, "OFF", true);
        }
      }
      if (digitalRead(pinFundos) == RELAY_ON) {
        digitalWrite(pinFundos, RELAY_OFF);
        if (client.connected()) {
          client.publish(state_fundos, "OFF", true);
        }
      }
    }

    // Fallback Local por Horário (Caso perca conexão com o Broker MQTT)
    if (WiFi.status() == WL_CONNECTED && !client.connected() && has_fallback_times && time(nullptr) > 1000000) {
      time_t now_unix = time(nullptr);
      struct tm* timeinfo = localtime(&now_unix);
      bool should_be_on = isFallbackNightTime(timeinfo->tm_hour, timeinfo->tm_min);
      
      if (should_be_on) {
        if (digitalRead(pinFrente) == RELAY_OFF) {
          digitalWrite(pinFrente, RELAY_ON);
          Serial.println("Fallback Local: Frente -> ON");
        }
        if (digitalRead(pinFundos) == RELAY_OFF) {
          digitalWrite(pinFundos, RELAY_ON);
          Serial.println("Fallback Local: Fundos -> ON");
        }
      } else {
        if (digitalRead(pinFrente) == RELAY_ON) {
          digitalWrite(pinFrente, RELAY_OFF);
          Serial.println("Fallback Local: Frente -> OFF");
        }
        if (digitalRead(pinFundos) == RELAY_ON) {
          digitalWrite(pinFundos, RELAY_OFF);
          Serial.println("Fallback Local: Fundos -> OFF");
        }
      }
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
