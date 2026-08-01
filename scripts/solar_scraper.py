import os
import sys
import json
import time
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

import subprocess
import socket
import concurrent.futures

DEFAULT_SOLAR_MAC = "98:cd:ac:1b:9d:79"
DEFAULT_SOLAR_IP = "192.168.1.13"
CACHE_IP_FILE = "/tmp/solar_inverter_cached_ip"

def get_inverter_mac():
    return os.getenv("SOLAR_INVERTER_MAC", DEFAULT_SOLAR_MAC).lower().strip()

def get_inverter_ip_hint():
    return os.getenv("SOLAR_INVERTER_IP", DEFAULT_SOLAR_IP).strip()

def find_ip_in_arp(target_mac):
    """
    Busca o IP correspondente ao MAC address informado na tabela ARP do sistema (/proc/net/arp / ip neighbor).
    """
    target_mac = target_mac.lower().strip()
    if os.path.exists('/proc/net/arp'):
        try:
            with open('/proc/net/arp', 'r') as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 4:
                        ip, hw_addr = parts[0], parts[3].lower()
                        if hw_addr == target_mac:
                            return ip
        except Exception:
            pass

    try:
        out = subprocess.check_output(['ip', 'neighbor'], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            parts = line.split()
            if 'lladdr' in parts:
                idx = parts.index('lladdr')
                if idx + 1 < len(parts) and parts[idx+1].lower() == target_mac:
                    return parts[0]
    except Exception:
        pass

    return None

def test_inverter_endpoint(ip, timeout=2):
    """
    Valida rapidamente se um dado IP responde com a assinatura do inversor solar.
    """
    try:
        url = f"http://{ip}/status/status.php"
        resp = requests.post(url, data={"t": "l"}, timeout=timeout)
        return resp.status_code == 200 and len(resp.text.strip().split(",")) == 35
    except Exception:
        return False

def scan_subnet_for_mac(target_mac, subnet_prefix="192.168.1."):
    """
    Realiza uma varredura paralela rápida na sub-rede para forçar atualização da tabela ARP e localizar o MAC.
    """
    target_mac = target_mac.lower().strip()
    ips = [f"{subnet_prefix}{i}" for i in range(1, 255)]

    def probe(ip):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                s.connect((ip, 80))
        except Exception:
            pass

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        list(executor.map(probe, ips))

    return find_ip_in_arp(target_mac)

def cache_working_ip(ip):
    try:
        with open(CACHE_IP_FILE, 'w') as f:
            f.write(ip)
    except Exception:
        pass

def resolve_inverter_ip():
    """
    Resolve dinamicamente o IP do inversor solar com resiliência baseada em MAC Address:
    1. Tenta o IP armazenado em cache local (/tmp/solar_inverter_cached_ip).
    2. Procura pelo MAC address na tabela ARP ativa (/proc/net/arp).
    3. Testa o IP hint configurado no .env.
    4. Se falhar, executa scan rápido na sub-rede para atualizar o ARP e localizar o MAC.
    """
    target_mac = get_inverter_mac()
    ip_hint = get_inverter_ip_hint()

    # 1. Tenta IP em cache
    if os.path.exists(CACHE_IP_FILE):
        try:
            with open(CACHE_IP_FILE, 'r') as f:
                cached_ip = f.read().strip()
                if cached_ip and test_inverter_endpoint(cached_ip):
                    return cached_ip
        except Exception:
            pass

    # 2. Busca na tabela ARP pelo MAC
    arp_ip = find_ip_in_arp(target_mac)
    if arp_ip and test_inverter_endpoint(arp_ip):
        cache_working_ip(arp_ip)
        return arp_ip

    # 3. Testa IP de hint configurado no .env
    if ip_hint and test_inverter_endpoint(ip_hint):
        cache_working_ip(ip_hint)
        return ip_hint

    # 4. Varredura de sub-rede se o IP mudou e a tabela ARP expirou
    scanned_ip = scan_subnet_for_mac(target_mac)
    if scanned_ip and test_inverter_endpoint(scanned_ip):
        logging.info(f"🔎 Inversor solar localizado no novo IP {scanned_ip} via MAC {target_mac}")
        cache_working_ip(scanned_ip)
        return scanned_ip

    return ip_hint

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
    Resolve o IP dinamicamente por MAC address caso o IP não seja especificado.
    Retorna um dicionário de telemetria se online, ou None se offline (sem sol).
    """
    if ip is None:
        ip = resolve_inverter_ip()

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

ANOMALY_THROTTLE_FILE = "/tmp/solar_anomalies_throttle.json"
ANOMALY_THROTTLE_SECONDS = 1800  # Rate-limiting de 30 minutos por anomalia

def check_solar_anomalies(telemetry, now_obj=None, dry_run=False):
    """
    Verifica a ocorrência de anomalias no inversor solar e envia alertas no Telegram.
    1. Status de erro no inversor (status != Normal)
    2. Sobretemperatura crítica (>= 60°C)
    3. Desconexão / Assimetria de String PV no pico solar (10h às 16h)
    Aplica trava de rate-limiting (throttle) de 30 minutos por tipo de anomalia.
    """
    if not telemetry:
        return []

    anomalies_detected = []
    now = now_obj or datetime.now(BR_TZ)
    current_hour = now.hour
    status = (telemetry.get("status") or "Normal").strip()
    temp = float(telemetry.get("temperature") or 0.0)
    pv1_v = float(telemetry.get("pv1_voltage") or 0.0)
    pv2_v = float(telemetry.get("pv2_voltage") or 0.0)
    power_w = float(telemetry.get("power_w") or 0.0)

    # 1. Falha de Status do Inversor
    if status.lower() not in ["normal", "online", "ok"]:
        anomalies_detected.append({
            "key": "inverter_fault",
            "title": "Falha / Alerta de Status no Inversor",
            "detail": f"Status reportado: `{status}`",
            "icon": "🚨"
        })

    # 2. Sobretemperatura (>= 60°C)
    if temp >= 60.0:
        anomalies_detected.append({
            "key": "high_temperature",
            "title": "Sobretemperatura Crítica no Inversor",
            "detail": f"Temperatura atual: `{temp:.1f} °C` (Limite: `60.0 °C`)",
            "icon": "🔥"
        })

    # 3. Desconexão / Assimetria de String PV (Horário de pico sol: 10h às 16h)
    if 10 <= current_hour <= 16:
        if pv1_v >= 80.0 and pv2_v < 15.0:
            anomalies_detected.append({
                "key": "pv_string_fault",
                "title": "Queda / Desconexão na String PV2",
                "detail": f"Tensão PV1: `{pv1_v:.1f} V` | Tensão PV2: `{pv2_v:.1f} V` (Anormal em pico sol)",
                "icon": "⚡"
            })
        elif pv2_v >= 80.0 and pv1_v < 15.0:
            anomalies_detected.append({
                "key": "pv_string_fault",
                "title": "Queda / Desconexão na String PV1",
                "detail": f"Tensão PV1: `{pv1_v:.1f} V` | Tensão PV2: `{pv2_v:.1f} V` (Anormal em pico sol)",
                "icon": "⚡"
            })

    if not anomalies_detected:
        return []

    # Carrega controle de throttle de alertas
    throttle_data = {}
    if os.path.exists(ANOMALY_THROTTLE_FILE):
        try:
            with open(ANOMALY_THROTTLE_FILE, "r") as f:
                throttle_data = json.load(f)
        except Exception:
            throttle_data = {}

    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_user_id = os.getenv("TELEGRAM_ALLOWED_USER_ID")
    now_ts = time.time()

    alerts_sent = []
    for anomaly in anomalies_detected:
        key = anomaly["key"]
        last_sent = throttle_data.get(key, 0)
        
        if dry_run or (now_ts - last_sent >= ANOMALY_THROTTLE_SECONDS):
            msg = (
                f"{anomaly['icon']} *ALERTA DE ANOMALIA SOLAR*\n\n"
                f"⚠️ *Anomalia:* `{anomaly['title']}`\n"
                f"📊 *Detalhe:* {anomaly['detail']}\n"
                f"⚡ *Potência Atual:* `{int(power_w)} W`\n"
                f"📅 *Horário:* `{now.strftime('%d/%m/%Y %H:%M:%S')}`"
            )
            logging.warning(f"🚨 Anomalia solar detectada [{key}]: {anomaly['title']}")

            if not dry_run and tg_token and tg_user_id:
                try:
                    requests.post(
                        f"https://api.telegram.org/bot{tg_token}/sendMessage",
                        json={"chat_id": tg_user_id, "text": msg, "parse_mode": "Markdown"},
                        timeout=10
                    )
                except Exception as e:
                    logging.error(f"Erro ao enviar alerta de anomalia no Telegram: {e}")

            if not dry_run:
                throttle_data[key] = now_ts

            alerts_sent.append(anomaly)

    if not dry_run:
        try:
            with open(ANOMALY_THROTTLE_FILE, "w") as f:
                json.dump(throttle_data, f)
        except Exception as e:
            logging.warning(f"Erro ao atualizar throttle file de anomalias: {e}")

    return alerts_sent

def run_solar_scraping_cycle(mqtt_client=None, conn=None, ip=None):
    """
    Ciclo principal de coleta de telemetria solar:
    1. Scraping via HTTP (POST status.php)
    2. Persistência no PostgreSQL
    3. Publicação no MQTT
    4. Checagem e Alerta de Anomalias no Telegram
    """
    telemetry = fetch_solar_telemetry(ip=ip)
    if telemetry:
        if conn:
            save_solar_telemetry(telemetry, conn)
        if mqtt_client:
            publish_solar_mqtt(telemetry, mqtt_client)
        try:
            check_solar_anomalies(telemetry)
        except Exception as ea:
            logging.error(f"Erro ao checar anomalias solares: {ea}")
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
