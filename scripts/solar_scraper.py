import os
import sys
import json
import logging
import requests
import psycopg2
from datetime import datetime, timedelta, timezone

# Fuso Horário Brasil (GMT-3)
BR_TZ = timezone(timedelta(hours=-3))

STATUS_MAP = {
    0: "Not connected",
    1: "Waiting",
    2: "Normal",
    3: "Error",
    4: "Upgrading"
}

def get_inverter_ip():
    return os.getenv("SOLAR_INVERTER_IP", "192.168.1.13")

def parse_solar_csv(csv_text):
    """
    Decodifica os 35 valores CSV retornados pelo endpoint status/status.php do inversor solar.
    Aplica os fatores de precisão (scale factors) correspondentes.
    """
    raw = csv_text.strip()
    data = raw.split(",")
    if len(data) != 35:
        raise ValueError(f"Resposta com formato inesperado. Esperado 35 campos, recebido {len(data)}: {raw}")

    def safe_val(val_str, scale=1.0, precision=2):
        if val_str == "65535" or val_str == "":
            return None
        try:
            val = float(val_str) * scale
            return round(val, precision)
        except (ValueError, TypeError):
            return None

    state_code = int(data[34]) if data[34].isdigit() else -1
    status_str = STATUS_MAP.get(state_code, "Unknown")

    telemetry = {
        "timestamp": datetime.now(BR_TZ).isoformat(),
        "total_kwh": safe_val(data[1], 0.01, 2),
        "total_hours": safe_val(data[2], 0.1, 1),
        "today_kwh": safe_val(data[3], 0.01, 2),
        "today_hours": safe_val(data[4], 0.1, 1),
        "pv1_voltage": safe_val(data[5], 0.1, 1),
        "pv1_current": safe_val(data[6], 0.01, 2),
        "pv2_voltage": safe_val(data[7], 0.1, 1),
        "pv2_current": safe_val(data[8], 0.01, 2),
        "power_w": safe_val(data[23], 1.0, 2) or 0.0,
        "grid_frequency": safe_val(data[24], 0.01, 2),
        "grid_voltage": safe_val(data[25], 0.1, 1),
        "grid_current": safe_val(data[26], 0.01, 2),
        "bus_voltage": safe_val(data[31], 0.1, 1),
        "temperature": safe_val(data[32], 0.1, 1),
        "co2_reduction_kg": safe_val(data[33], 0.1, 1),
        "state_code": state_code,
        "status": status_str,
        "raw_csv": raw
    }
    return telemetry

def fetch_solar_telemetry(ip=None, timeout=5):
    """
    Solicita a telemetria do inversor via requisição HTTP POST.
    Retorna um dicionário de telemetria se online, ou None se offline (sem sol).
    """
    if ip is None:
        ip = get_inverter_ip()

    url = f"http://{ip}/status/status.php"
    try:
        response = requests.post(url, data={"t": "l"}, timeout=timeout)
        if response.status_code == 200:
            return parse_solar_csv(response.text)
        else:
            logging.warning(f"Inversor solar ({ip}) retornou código HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        # Quando não há sol, a interface web do inversor se desliga e não responde
        logging.debug(f"Inversor solar ({ip}) offline ou inacessível (sem sol): {e}")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao realizar scraping do inversor ({ip}): {e}")
        return None

def init_solar_db(conn):
    """
    Garante que a tabela solar_generation exista no banco PostgreSQL.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS solar_generation (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    power_w NUMERIC(10, 2) NOT NULL DEFAULT 0,
                    today_kwh NUMERIC(10, 2) NOT NULL DEFAULT 0,
                    total_kwh NUMERIC(10, 2) NOT NULL DEFAULT 0,
                    pv1_voltage NUMERIC(6, 2),
                    pv1_current NUMERIC(6, 2),
                    pv2_voltage NUMERIC(6, 2),
                    pv2_current NUMERIC(6, 2),
                    grid_voltage NUMERIC(6, 2),
                    grid_current NUMERIC(6, 2),
                    grid_frequency NUMERIC(5, 2),
                    temperature NUMERIC(5, 2),
                    status VARCHAR(20) DEFAULT 'Normal',
                    raw_csv TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_solar_gen_timestamp ON solar_generation(timestamp DESC);
            """)
        conn.commit()
    except Exception as e:
        logging.error(f"Erro ao inicializar tabela solar_generation: {e}")
        try:
            conn.rollback()
        except Exception:
            pass

def save_solar_telemetry(telemetry, conn):
    """
    Persiste o registro de telemetria solar na tabela solar_generation.
    """
    if not telemetry or not conn:
        return None

    try:
        init_solar_db(conn)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO solar_generation (
                    timestamp, power_w, today_kwh, total_kwh,
                    pv1_voltage, pv1_current, pv2_voltage, pv2_current,
                    grid_voltage, grid_current, grid_frequency, temperature,
                    status, raw_csv
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s
                ) RETURNING id;
            """, (
                telemetry["timestamp"],
                telemetry["power_w"],
                telemetry["today_kwh"] or 0,
                telemetry["total_kwh"] or 0,
                telemetry["pv1_voltage"],
                telemetry["pv1_current"],
                telemetry["pv2_voltage"],
                telemetry["pv2_current"],
                telemetry["grid_voltage"],
                telemetry["grid_current"],
                telemetry["grid_frequency"],
                telemetry["temperature"],
                telemetry["status"],
                telemetry["raw_csv"]
            ))
            row_id = cur.fetchone()[0]
        conn.commit()
        logging.info(f"☀️ Geração Solar gravada no DB: {telemetry['power_w']} W, Hoje: {telemetry['today_kwh']} kWh [ID: {row_id}]")
        return row_id
    except Exception as e:
        logging.error(f"Erro ao salvar telemetria solar no DB: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None

def publish_solar_mqtt(telemetry, mqtt_client):
    """
    Publica os dados de geração solar nos tópicos MQTT correspondentes.
    """
    if not mqtt_client:
        return

    try:
        if telemetry:
            mqtt_client.publish("home/solar/telemetry", json.dumps(telemetry), qos=1, retain=True)
            mqtt_client.publish("home/solar/power_w", str(telemetry["power_w"]), qos=1, retain=True)
            mqtt_client.publish("home/solar/today_kwh", str(telemetry["today_kwh"] or 0), qos=1, retain=True)
            mqtt_client.publish("home/solar/status", telemetry["status"], qos=1, retain=True)
        else:
            mqtt_client.publish("home/solar/status", "Offline", qos=1, retain=True)
            mqtt_client.publish("home/solar/power_w", "0.0", qos=1, retain=True)
    except Exception as e:
        logging.error(f"Erro ao publicar telemetria solar no MQTT: {e}")

def run_solar_scraping_cycle(mqtt_client=None, conn=None, ip=None):
    """
    Ciclo principal de coleta de telemetria solar:
    1. Scraping via HTTP (POST status.php)
    2. Persistência no PostgreSQL
    3. Publicação no MQTT
    """
    telemetry = fetch_solar_telemetry(ip=ip)
    if telemetry:
        if conn:
            save_solar_telemetry(telemetry, conn)
        if mqtt_client:
            publish_solar_mqtt(telemetry, mqtt_client)
    else:
        if mqtt_client:
            publish_solar_mqtt(None, mqtt_client)
    return telemetry

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - SOLAR_SCRAPER - %(message)s')
    print("==> Testando Scraping do Inversor Solar...")
    ip = get_inverter_ip()
    print(f"Target IP: {ip}")
    res = fetch_solar_telemetry(ip)
    if res:
        print("\n✅ Telemetria obtida com sucesso:")
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("\n⚠️ Inversor solar offline ou não respondeu na LAN (Sem Sol).")
