#include <WiFi.h>
#include <PubSubClient.h>
#include <time.h>
#include <sys/time.h>

// ==========================================
// Configurações de Wi-Fi
// ==========================================
const char* ssid = "ZN-BRUNO_CONTER";
const char* password = "veracruz";

// Configuração de IP Estático
IPAddress local_IP(192, 168, 1, 112);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(192, 168, 1, 7);  // unbound localserver
IPAddress secondaryDNS(1, 1, 1, 1);    // Cloudflare fallback

// ==========================================
// Configurações de MQTT
// ==========================================
const char* mqtt_server = "192.168.1.7";
const int mqtt_port = 1883;
const char* mqtt_user = "bruno";
const char* mqtt_password = "blurbang";

// Lógica Invertida de Relé (Active Low)
#define RELAY_ON LOW
#define RELAY_OFF HIGH

#define FW_VERSION "2026.11.3-c3"

// ==========================================
// Mapeamento de Pinos - ESP32-C3 Supermini
// ==========================================
// GPIO4 e GPIO5: Livres de strapping de boot e sem conflito de pullups
const int pinMuro = 4;
const int pinAux  = 5;

// LED On-board do ESP32-C3 Supermini (GPIO8, Active Low)
const int pinLed  = 8;
#define LED_ON  LOW
#define LED_OFF HIGH

// ==========================================
// Tópicos MQTT
// ==========================================
const char* set_muro = "home/outdoor/muro/set";
const char* state_muro = "home/outdoor/muro/state";

const char* set_aux = "home/outdoor/aux/set";
const char* state_aux = "home/outdoor/aux/state";

const char* muro_reboot = "home/outdoor/muro/reboot";
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
unsigned long lastTimeSyncMillis = 0;
unsigned long mqttConnectedAt = 0;
bool bootGracePeriod = true;
#define BOOT_GRACE_MS 4000
bool isClockSynced = false;

int fallback_on_hour = 18;
int fallback_on_minute = 15;
int fallback_off_hour = 7;
int fallback_off_minute = 30;
bool has_fallback_times = false;

bool isFallbackNightTime(int cur_hour, int cur_min) {
  int cur_total = cur_hour * 60 + cur_min;
  int on_total = fallback_on_hour * 60 + fallback_on_minute;
  int off_total = fallback_off_hour * 60 + fallback_off_minute;

  if (on_total > off_total) {
    return (cur_total >= on_total || cur_total < off_total);
  } else {
    return (cur_total >= on_total && cur_total < off_total);
  }
}

void setup_time() {
  setenv("TZ", "BRT3", 1);
  tzset();
  Serial.println("Timezone GMT-3 (BRT3) configurado. Sincronizacao de tempo via MQTT.");
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

  Serial.print("\n[ESP32-C3] Configurando IP Estatico: ");
  Serial.println(local_IP);

  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
    Serial.println("Falha ao configurar IP Estatico");
  }

  Serial.print("Conectando ao Wi-Fi: ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 25) {
    delay(400);
    digitalWrite(pinLed, !digitalRead(pinLed)); // Pisca LED durante busca de Wi-Fi
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    digitalWrite(pinLed, LED_ON); // LED aceso fixo = Wi-Fi Conectado
    Serial.println("\nWiFi OK! IP: " + WiFi.localIP().toString());
  } else {
    digitalWrite(pinLed, LED_OFF);
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String messageTemp = "";
  for (int i = 0; i < length; i++) messageTemp += (char)payload[i];
  messageTemp.trim();

  if (String(topic) == set_muro) {
    if (bootGracePeriod && (millis() - mqttConnectedAt < BOOT_GRACE_MS)) {
      Serial.println("[MQTT] Comando set_muro retido no boot ignorado. Mantendo OFF.");
      client.publish(state_muro, "OFF", true);
      return;
    }
    if (messageTemp == "ON") {
      digitalWrite(pinMuro, RELAY_ON);
      client.publish(state_muro, "ON", true);
      Serial.println("[MQTT] Muro -> ON");
    } else if (messageTemp == "OFF") {
      digitalWrite(pinMuro, RELAY_OFF);
      client.publish(state_muro, "OFF", true);
      Serial.println("[MQTT] Muro -> OFF");
    }
  } else if (String(topic) == set_aux) {
    if (bootGracePeriod && (millis() - mqttConnectedAt < BOOT_GRACE_MS)) {
      Serial.println("[MQTT] Comando set_aux retido no boot ignorado. Mantendo OFF.");
      client.publish(state_aux, "OFF", true);
      return;
    }
    if (messageTemp == "ON") {
      digitalWrite(pinAux, RELAY_ON);
      client.publish(state_aux, "ON", true);
      Serial.println("[MQTT] Aux -> ON");
    } else if (messageTemp == "OFF") {
      digitalWrite(pinAux, RELAY_OFF);
      client.publish(state_aux, "OFF", true);
      Serial.println("[MQTT] Aux -> OFF");
    }
  } else if (String(topic) == muro_reboot) {
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
        Serial.printf("Fallback ON recebido: %02d:%02d\n", fallback_on_hour, fallback_on_minute);
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
        Serial.printf("Fallback OFF recebido: %02d:%02d\n", fallback_off_hour, fallback_off_minute);
      }
    }
  } else if (String(topic) == time_topic) {
    long long epoch = messageTemp.toInt();
    if (epoch > 1700000000) {
      struct timeval tv;
      tv.tv_sec = epoch;
      tv.tv_usec = 0;
      settimeofday(&tv, nullptr);
      setenv("TZ", "BRT3", 1);
      tzset();
      lastTimeSyncMillis = millis();
      isClockSynced = true;
      Serial.print("Relogio local ajustado via MQTT para: ");
      Serial.println((long)epoch);
    }
  }
}

boolean reconnect() {
  Serial.print("Tentando MQTT (ESP32-C3 Muro)... ");
  String clientId = "ESP32C3-Muro-" + String(random(0xffff), HEX);

  if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
    Serial.println("CONECTADO!");
    digitalWrite(pinLed, LED_ON);
    mqttConnectedAt = millis();

    client.subscribe(set_muro);
    client.subscribe(set_aux);
    client.subscribe(muro_reboot);
    client.subscribe(fallback_on_topic);
    client.subscribe(fallback_off_topic);
    client.subscribe(time_topic);

    // Publica estado atual ao reconectar para manter sincronismo
    client.publish(state_muro, (digitalRead(pinMuro) == RELAY_ON ? "ON" : "OFF"), true);
    client.publish(state_aux, (digitalRead(pinAux) == RELAY_ON ? "ON" : "OFF"), true);
  } else {
    Serial.print("Falhou, rc=");
    Serial.println(client.state());
  }
  return client.connected();
}

void setup() {
  Serial.begin(115200);

  // No ESP32, digitalWrite() antes de pinMode() NAO define o nivel. Para evitar pulso ON (Active Low)
  // no boot: habilita pull-up (nivel HIGH = desligado), configura OUTPUT e escreve RELAY_OFF.
  pinMode(pinMuro, INPUT_PULLUP);
  pinMode(pinAux, INPUT_PULLUP);
  pinMode(pinLed, INPUT_PULLUP);
  pinMode(pinMuro, OUTPUT);
  pinMode(pinAux, OUTPUT);
  pinMode(pinLed, OUTPUT);
  digitalWrite(pinMuro, RELAY_OFF);
  digitalWrite(pinAux, RELAY_OFF);
  digitalWrite(pinLed, LED_OFF);

  setup_wifi();

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  if (WiFi.status() == WL_CONNECTED) {
    setup_time();
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

  // 2. Política de Conexão com o Broker MQTT
  if (WiFi.status() == WL_CONNECTED) {
    // HealthCheck a cada 5 minutos
    if (now - lastHealthCheck > 300000) {
      lastHealthCheck = now;
      if (client.connected()) {
        if (!client.publish("home/outdoor/heartbeat", "check_c3")) {
          Serial.println("[HealthCheck] Falha no ping MQTT. Desconectando...");
          client.disconnect();
        }
      }
    }

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

      if (bootGracePeriod && mqttConnectedAt > 0 && (now - mqttConnectedAt >= BOOT_GRACE_MS)) {
        bootGracePeriod = false;
        Serial.println("[MQTT] Boot grace period finalizado. Pronto para novos comandos.");
      }
    }
  }

  // Watchdog local de Autocura (10 minutos sem conexao reinicia a placa)
  if (now - lastWiFiConnected > 600000 || now - lastMqttConnected > 600000) {
    Serial.println("🚨 Watchdog local disparado! Sem conexao por mais de 10 min. Reiniciando...");
    delay(1000);
    ESP.restart();
  }

  // 3. Heartbeat e Telemetria (a cada 60s)
  if (now - lastMsg > 60000) {
    lastMsg = now;

    unsigned long mqtt_offline_duration = (lastMqttConnected > 0 && now > lastMqttConnected) ? (now - lastMqttConnected) : 0;
    bool is_mqtt_offline_sustained = (!client.connected() && mqtt_offline_duration > 120000);
    bool is_clock_fresh = (isClockSynced && (now - lastTimeSyncMillis < 900000));

    // Fallback de Segurança Noturno/Diurno caso desconectado sustentado
    if (WiFi.status() == WL_CONNECTED && is_mqtt_offline_sustained && is_clock_fresh && !isNightTime() && time(nullptr) > 1000000) {
      if (digitalRead(pinMuro) == RELAY_ON) digitalWrite(pinMuro, RELAY_OFF);
      if (digitalRead(pinAux) == RELAY_ON) digitalWrite(pinAux, RELAY_OFF);
    }

    if (client.connected()) {
      time_t now_sec = time(nullptr);
      struct tm* timeinfo = localtime(&now_sec);
      char hhmm_buf[6] = "??:??";
      if (now_sec > 1000000 && timeinfo != nullptr) {
        snprintf(hhmm_buf, sizeof(hhmm_buf), "%02d:%02d", timeinfo->tm_hour, timeinfo->tm_min);
      }
      unsigned long uptime_sec = millis() / 1000;

      String q = String((char)34);
      String payload = "{";
      payload += q + "status" + q + ":" + q + "online" + q + ",";
      payload += q + "device" + q + ":" + q + "esp32_muro" + q + ",";
      payload += q + "muro" + q + ":" + q + (digitalRead(pinMuro) == RELAY_ON ? "ON" : "OFF") + q + ",";
      payload += q + "aux" + q + ":" + q + (digitalRead(pinAux) == RELAY_ON ? "ON" : "OFF") + q + ",";
      payload += q + "rssi" + q + ":" + String(WiFi.RSSI()) + ",";
      payload += q + "ip" + q + ":" + q + WiFi.localIP().toString() + q + ",";
      payload += q + "uptime_s" + q + ":" + String(uptime_sec) + ",";
      payload += q + "hhmm" + q + ":" + q + String(hhmm_buf) + q + ",";
      payload += q + "synced" + q + ":" + (isClockSynced ? "true" : "false") + ",";
      payload += q + "fw" + q + ":" + q + FW_VERSION + q;
      payload += "}";
      client.publish(status_topic, payload.c_str());
    }
  }
}
