import os
import time
import json
import requests
import psycopg2
import logging
import threading
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta, date, timezone
from dotenv import load_dotenv

# Carrega configurações
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SOLAR_WORKER - %(message)s')

# Configurações
LAT = os.getenv("LATITUDE")
LONG = os.getenv("LONGITUDE")
MQTT_BROKER = os.getenv("MQTT_BROKER", "192.168.1.7")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASSWORD")
CACHE_FILE = os.path.join(os.path.dirname(__file__), "sun_cache.json")

# Telegram
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")

# Fuso Horário Brasil (GMT-3)
BR_TZ = timezone(timedelta(hours=-3))

LAST_SEEN_FILE = "/tmp/wemos_last_seen"

# Estado global em memória
current_states = {} 
last_hour_logged = -1
db_conn = None
db_lock = threading.Lock()

def send_telegram_message(text):
    """Envia uma notificação para o Telegram via requisição HTTP direta."""
    if not TG_TOKEN or not TG_USER_ID:
        return

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_USER_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        # Timeout curto para não atrasar o ciclo principal do worker
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            logging.error(f"Erro ao enviar Telegram: {response.text}")
    except Exception as e:
        logging.error(f"Falha na conexão com Telegram: {e}")

def touch_last_seen():
    """Atualiza o timestamp local de última atividade do Wemos."""
    try:
        with open(LAST_SEEN_FILE, 'w') as f:
            f.write(str(time.time()))
    except Exception as e:
        logging.error(f"Erro ao atualizar last_seen: {e}")

def get_db_conn():
    global db_conn
    with db_lock:
        try:
            if db_conn is None or db_conn.closed:
                db_conn = psycopg2.connect(
                    host=os.getenv("POSTGRES_HOST", "localhost"),
                    database=os.getenv("POSTGRES_DB", "light_manager"),
                    user=os.getenv("POSTGRES_USER", "brunoconter"),
                    password=os.getenv("POSTGRES_PASSWORD")
                )
                # Garante que a sessão do banco use o fuso horário correto
                with db_conn.cursor() as cur:
                    cur.execute("SET timezone TO 'America/Sao_Paulo';")
            return db_conn
        except Exception as e:
            logging.error(f"Erro ao conectar ao banco: {e}")
            db_conn = None
            return None

def log_event_to_db(topic, state, source="mqtt_capture", cursor=None):
    """Salva um evento de estado no banco de dados com fonte e timestamp correto."""
    local_cur = None
    try:
        conn = get_db_conn()
        if not conn: return

        cur = cursor if cursor else conn.cursor()
        if not cursor: local_cur = cur

        base_topic = topic.replace("/state", "").replace("/set", "")
        
        # Timestamp atual em GMT-3 (Aware object)
        now_br = datetime.now(BR_TZ)
        
        cur.execute("SELECT id FROM light_points WHERE mqtt_topic = %s", (base_topic,))
        res = cur.fetchone()
        if res:
            point_id = res[0]
            cur.execute(
                "INSERT INTO light_events (point_id, event_type, source, timestamp) VALUES (%s, %s, %s, %s)",
                (point_id, state, source, now_br)
            )
            # Commit after each event to maintain independence and avoid transaction poisoning
            conn.commit()
            logging.info(f"💾 Registrado no DB [{source}]: {base_topic} -> {state}")

    except Exception as e:
        logging.error(f"❌ Erro ao logar no DB: {e}")
        try:
            conn = get_db_conn()
            if conn: conn.rollback()
        except: pass
    finally:
        if local_cur:
            local_cur.close()

def on_connect(client, userdata, flags, rc, properties):
    logging.info(f"Conectado ao Broker com resultado: {rc}")
    client.subscribe("home/outdoor/+/state")
    client.subscribe("home/outdoor/status")

def on_message(client, userdata, msg):
    touch_last_seen()
    
    if "/status" in msg.topic:
        return # Heartbeat apenas atualiza o arquivo, não vai pro DB
        
    topic = msg.topic.replace("/state", "")
    state = msg.payload.decode()
    
    if current_states.get(topic) != state:
        current_states[topic] = state
        log_event_to_db(topic, state, source="mqtt_capture")

def fetch_sun_data_with_retry(max_retries=5):
    url = f"https://api.sunrise-sunset.org/json?lat={LAT}&lng={LONG}&formatted=0"
    for i in range(max_retries):
        try:
            res = requests.get(url, timeout=10).json()
            if res["status"] == "OK":
                with open(CACHE_FILE, 'w') as f:
                    json.dump({"date": str(date.today()), "results": res["results"]}, f)
                return res["results"]
        except:
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
    
    now_br = datetime.now(BR_TZ)
    sunrise_br = sunrise_utc.astimezone(BR_TZ)
    sunset_br = sunset_utc.astimezone(BR_TZ)
    
    current_time_str = now_br.strftime("%H:%M")
    current_hour = now_br.hour

    cur = None
    try:
        conn = get_db_conn()
        if not conn: return
        cur = conn.cursor()

        if current_hour != last_hour_logged:
            logging.info(f"⏰ Verificação Horária: {current_hour}:00")
            # Usa .copy() para evitar erro de 'dictionary changed size during iteration'
            for topic, state in current_states.copy().items():
                log_event_to_db(topic, state, source="hourly_snapshot", cursor=cur)
            last_hour_logged = current_hour

        cur.execute("SELECT mqtt_topic, offset_on_minutes, offset_off_minutes FROM light_points WHERE auto_mode = TRUE")
        points = cur.fetchall()
        
        for topic, off_on, off_off in points:
            # Calcula horários exatos de hoje para este ponto
            on_dt = sunset_br + timedelta(minutes=off_on)
            off_dt = sunrise_br + timedelta(minutes=off_off)
            
            # Formatação para comparação de minuto exato (gatilho de log/notificação)
            target_on_str = on_dt.strftime("%H:%M")
            target_off_str = off_dt.strftime("%H:%M")
            
            # Lógica de determinação do estado desejado (entre ON e OFF)
            # Se off_dt for antes de on_dt (ex: 06:00 e 18:00), estamos ON se: agora > on_dt OU agora < off_dt
            is_night = False
            if on_dt < off_dt: # Caso raro dependendo dos offsets
                is_night = on_dt <= now_br < off_dt
            else: # Caso comum: liga fim do dia, desliga começo do outro
                is_night = now_br >= on_dt or now_br < off_dt

            desired_state = "ON" if is_night else "OFF"
            current_state = current_states.get(topic)

            # 1. Gatilho de Minuto Exato (Log e Telegram)
            if current_time_str == target_on_str:
                logging.info(f"🌑 Gatilho Solar: LIGANDO {topic}")
                client.publish(f"{topic}/set", "ON", retain=True)
                log_event_to_db(topic, "ON", source="solar_trigger", cursor=cur)
                send_telegram_message(f"🌑 *Gatilho Solar*\nLuz: `{topic}`\nAção: `LIGAR` 💡")
            elif current_time_str == target_off_str:
                logging.info(f"🌅 Gatilho Solar: DESLIGANDO {topic}")
                client.publish(f"{topic}/set", "OFF", retain=True)
                log_event_to_db(topic, "OFF", source="solar_trigger", cursor=cur)
                send_telegram_message(f"🌅 *Gatilho Solar*\nLuz: `{topic}`\nAção: `DESLIGAR` 🌑")
            
            # 2. Reforço de Estado (Fallback para queda de energia ou hardware offline)
            # Se o estado atual conhecido é diferente do desejado, reforçamos o comando
            if current_state and current_state != desired_state:
                logging.warning(f"⚠️ Desvio detectado em {topic}: Atual={current_state}, Desejado={desired_state}. Reforçando...")
                client.publish(f"{topic}/set", desired_state, retain=True)

    except Exception as e:
        logging.error(f"Erro no ciclo: {e}")
        try:
            conn = get_db_conn()
            if conn: conn.rollback()
        except: pass
    finally:
        if cur:
            cur.close()

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
        
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    logging.info(f"Serviço Solar & Event Logger iniciado (Fuso: GMT-3)")
    
    while True:
        run_automation_cycle(client)
        time.sleep(60)
