import os
import time
import json
import requests
import psycopg2
import logging
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta, date
from dotenv import load_dotenv

# Carrega configurações
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SOLAR_WORKER - %(message)s')

# Configurações
LAT = os.getenv("LATITUDE")
LONG = os.getenv("LONGITUDE")
MQTT_BROKER = os.getenv("MQTT_BROKER", "192.168.1.7")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER", "bruno")
MQTT_PASS = os.getenv("MQTT_PASSWORD", "blurbang")
CACHE_FILE = os.path.join(os.path.dirname(__file__), "sun_cache.json")

# Estado global em memória
current_states = {} # { "home/outdoor/frente": "OFF", ... }
last_hour_logged = -1

def get_db_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "light_manager"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "secret")
    )

def log_event_to_db(topic, state):
    """Salva um evento de estado no banco de dados."""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        # Remove '/state' ou '/set' se houver
        base_topic = topic.replace("/state", "").replace("/set", "")
        
        cur.execute("SELECT id FROM light_points WHERE mqtt_topic = %s", (base_topic,))
        res = cur.fetchone()
        if res:
            point_id = res[0]
            cur.execute(
                "INSERT INTO light_events (point_id, event_type) VALUES (%s, %s)",
                (point_id, state)
            )
            conn.commit()
            logging.info(f"💾 Registrado no DB: {base_topic} -> {state}")
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"❌ Erro ao logar no DB: {e}")

def on_connect(client, userdata, flags, rc, properties):
    logging.info(f"Conectado ao Broker com resultado: {rc}")
    # Assina os tópicos de estado para monitoramento em tempo real
    client.subscribe("home/outdoor/+/state")

def on_message(client, userdata, msg):
    topic = msg.topic.replace("/state", "")
    state = msg.payload.decode()
    current_states[topic] = state
    # Sempre que o estado mudar via MQTT, registramos no histórico
    log_event_to_db(topic, state)

def fetch_sun_data_with_retry(max_retries=5):
    url = f"https://api.sunrise-sunset.org/json?lat={LAT}&lng={LONG}&formatted=0"
    for i in range(max_retries):
        try:
            res = requests.get(url, timeout=10).json()
            if res["status"] == "OK":
                with open(CACHE_FILE, 'w') as f:
                    json.dump({"date": str(date.today()), "results": res["results"]}, f)
                return res["results"]
        except Exception as e:
            time.sleep(2 ** i)
    return None

def get_today_sun_data():
    today_str = str(date.today())
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                if data.get("date") == today_str:
                    return data["results"]
        except: pass
    return fetch_sun_data_with_retry()

def run_automation_cycle(client):
    global last_hour_logged
    sun_results = get_today_sun_data()
    if not sun_results: return

    sunrise_utc = datetime.fromisoformat(sun_results["sunrise"])
    sunset_utc = datetime.fromisoformat(sun_results["sunset"])
    
    now = datetime.now(sunrise_utc.tzinfo)
    current_time_str = now.strftime("%H:%M")
    current_hour = now.hour

    # 1. Registro Horário (Snapshot)
    if current_hour != last_hour_logged:
        logging.info(f"⏰ Verificação Horária: {current_hour}:00")
        for topic, state in current_states.items():
            log_event_to_db(topic, state)
        last_hour_logged = current_hour

    # 2. Lógica Solar
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT mqtt_topic, offset_on_minutes, offset_off_minutes FROM light_points WHERE auto_mode = TRUE")
        points = cur.fetchall()
        cur.close()
        conn.close()
        
        for topic, off_on, off_off in points:
            target_on = (sunset_utc + timedelta(minutes=off_on)).strftime("%H:%M")
            target_off = (sunrise_utc + timedelta(minutes=off_off)).strftime("%H:%M")

            if current_time_str == target_on:
                logging.info(f"🌑 Gatilho Solar: LIGANDO {topic}")
                client.publish(f"{topic}/set", "ON")
            elif current_time_str == target_off:
                logging.info(f"🌅 Gatilho Solar: DESLIGANDO {topic}")
                client.publish(f"{topic}/set", "OFF")
    except Exception as e:
        logging.error(f"Erro no ciclo: {e}")

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
        
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    logging.info("Serviço Solar & Event Logger iniciado.")
    
    while True:
        run_automation_cycle(client)
        time.sleep(60)
