import os
import time
import json
import requests
import psycopg2
import logging
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import paho.mqtt.publish as publish

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SOLAR_WORKER - %(message)s')

# Configurações
LAT = os.getenv("LATITUDE")
LONG = os.getenv("LONGITUDE")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
CACHE_FILE = os.path.join(os.path.dirname(__file__), "sun_cache.json")

def get_db_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "light_manager"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "secret")
    )

def fetch_sun_data_with_retry(max_retries=5):
    """Busca dados da API com lógica de retry exponencial."""
    url = f"https://api.sunrise-sunset.org/json?lat={LAT}&lng={LONG}&formatted=0"
    
    for i in range(max_retries):
        try:
            logging.info(f"Tentando buscar dados solares via API (Tentativa {i+1})...")
            res = requests.get(url, timeout=10).json()
            if res["status"] == "OK":
                # Salva o JSON bruto no arquivo para persistência entre reboots
                with open(CACHE_FILE, 'w') as f:
                    json.dump({
                        "date": str(date.today()),
                        "results": res["results"]
                    }, f)
                logging.info(f"✅ Dados solares salvos em {CACHE_FILE}")
                return res["results"]
        except Exception as e:
            logging.error(f"Erro na API (Tentativa {i+1}): {e}")
            time.sleep(2 ** i)
            
    return None

def get_today_sun_data():
    """
    Tenta ler do arquivo local primeiro. 
    Se o arquivo não existir ou for de outro dia, busca na API.
    """
    today_str = str(date.today())
    
    # 1. Tenta carregar do arquivo
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                if data.get("date") == today_str:
                    logging.info("📁 Usando cache local (sun_cache.json)")
                    return data["results"]
                else:
                    logging.info("📅 Cache antigo detectado. Necessário nova consulta.")
        except Exception as e:
            logging.error(f"Erro ao ler cache file: {e}")

    # 2. Se chegou aqui, precisa buscar na API
    return fetch_sun_data_with_retry()

def run_automation_cycle():
    sun_results = get_today_sun_data()
    if not sun_results:
        logging.warning("⚠️ Pulando ciclo: Impossível obter horários solares.")
        return

    # Parse dos horários (ISO strings)
    sunrise_utc = datetime.fromisoformat(sun_results["sunrise"])
    sunset_utc = datetime.fromisoformat(sun_results["sunset"])

    # Conecta ao banco para ver os pontos ativos
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT mqtt_topic, offset_on_minutes, offset_off_minutes FROM light_points WHERE auto_mode = TRUE")
        points = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Erro ao consultar DB: {e}")
        return

    # Compara horários
    now_utc = datetime.now(sunrise_utc.tzinfo)
    current_time_str = now_utc.strftime("%H:%M")

    for topic, off_on, off_off in points:
        target_on = (sunset_utc + timedelta(minutes=off_on)).strftime("%H:%M")
        target_off = (sunrise_utc + timedelta(minutes=off_off)).strftime("%H:%M")

        if current_time_str == target_on:
            logging.info(f"🌑 Gatilho Solar: LIGANDO {topic}")
            publish.single(f"{topic}/set", "ON", hostname=MQTT_BROKER, port=MQTT_PORT)
            
        elif current_time_str == target_off:
            logging.info(f"🌅 Gatilho Solar: DESLIGANDO {topic}")
            publish.single(f"{topic}/set", "OFF", hostname=MQTT_BROKER, port=MQTT_PORT)

if __name__ == "__main__":
    logging.info(f"Iniciando Autômato Solar (Persistente) para coordenadas: {LAT}, {LONG}")
    
    while True:
        run_automation_cycle()
        # Aguarda até o próximo minuto
        time.sleep(60)
