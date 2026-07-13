import os
import requests
import psycopg2
from psycopg2 import pool
import json
from datetime import date
from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
import asyncio
from pydantic import BaseModel
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
import time
import threading

# Carrega o .env da raiz do projeto
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

app = FastAPI()

# Permite que o frontend acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações
MQTT_BROKER = os.getenv("MQTT_BROKER", "192.168.1.7")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASSWORD")

LAT = os.getenv("LATITUDE", "0")
LONG = os.getenv("LONGITUDE", "0")

DISTRIBUTOR_SLUG = os.getenv("ENERGY_DISTRIBUTOR_SLUG")
try:
    TAX_RATE = float(os.getenv("ENERGY_TAX_RATE", "0.0"))
except ValueError:
    TAX_RATE = 0.0

# Cache de estados
light_states = {}
SUN_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'sun_cache.json')
sun_cache = {"date": None, "results": None}

# MQTT Setup
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def on_connect(client, userdata, flags, rc, properties):
    print(f"Conectado ao MQTT Broker com resultado: {rc}")
    client.subscribe("home/outdoor/+/state")
    client.subscribe("home/outdoor/+/log")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    
    if topic.endswith("/state"):
        light_states[topic] = payload
        print(f"Estado recebido: {topic} -> {payload}")
    elif topic.endswith("/log"):
        try:
            device_name = topic.split("/")[-2]
            log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_file_path = os.path.join(log_dir, 'devices.log')
            
            from datetime import datetime, timezone, timedelta
            sp_tz = timezone(timedelta(hours=-3))
            now_str = datetime.now(sp_tz).strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"[{now_str}] [{device_name.upper()}] {payload}\n")
        except Exception as e:
            print(f"Erro ao salvar log do dispositivo: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Configura credenciais se fornecidas
if MQTT_USER and MQTT_PASS:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)

try:
    print(f"Conectando ao broker {MQTT_BROKER}:{MQTT_PORT}...")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"Erro ao conectar no MQTT: {e}")
    # Não travamos a inicialização da API, mas o MQTT ficará offline

# DB Pooling (Lazy Initialization - Thread-Safe)
db_pool = None
db_pool_lock = threading.Lock()

def get_db_pool():
    global db_pool
    if db_pool is None:
        with db_pool_lock:
            if db_pool is None:
                db_pool = pool.ThreadedConnectionPool(
                    1, 10,
                    host=os.getenv("POSTGRES_HOST", "localhost"),
                    database=os.getenv("POSTGRES_DB", "light_manager"),
                    user=os.getenv("POSTGRES_USER", "postgres"),
                    password=os.getenv("POSTGRES_PASSWORD"),
                    port=os.getenv("POSTGRES_PORT", "5433")
                )
    return db_pool

def get_db_conn():
    return get_db_pool().getconn()

def release_db_conn(conn):
    get_db_pool().putconn(conn)

class CommandRequest(BaseModel):
    topic: str
    action: str

class PointConfigUpdate(BaseModel):
    offset_on_minutes: int
    offset_off_minutes: int

class PointCreate(BaseModel):
    name: str
    mqtt_topic: str
    power_w: float

class PasswordCheck(BaseModel):
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(req: LoginRequest):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT hashed_password, username FROM users WHERE username = %s", (req.username,))
        user = cur.fetchone()
        cur.close()

        if user:
            hashed_password = user[0]
            # Verifica a senha usando bcrypt diretamente
            if bcrypt.checkpw(req.password.encode('utf-8'), hashed_password.encode('utf-8')):
                return {"status": "ok", "username": user[1]}
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        release_db_conn(conn)

@app.post("/api/config/check_password")
def check_password(req: PasswordCheck):
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
    if req.password == admin_pass:
        return {"status": "ok"}
    raise HTTPException(status_code=401, detail="Invalid password")

@app.get("/api/config/points")
def get_points_config():
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, mqtt_topic, offset_on_minutes, offset_off_minutes, power_w FROM light_points ORDER BY name")
        points = cur.fetchall()
        cur.close()
        return [{
            "id": p[0], "name": p[1], "topic": p[2], 
            "offset_on": p[3], "offset_off": p[4], "power": float(p[5])
        } for p in points]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        release_db_conn(conn)

@app.put("/api/config/points/{point_id}")
def update_point_config(point_id: int, config: PointConfigUpdate):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE light_points SET offset_on_minutes = %s, offset_off_minutes = %s WHERE id = %s",
            (config.offset_on_minutes, config.offset_off_minutes, point_id)
        )
        conn.commit()
        cur.close()
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        release_db_conn(conn)

@app.post("/api/config/points")
def create_point(point: PointCreate):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO light_points (name, mqtt_topic, power_w) VALUES (%s, %s, %s) RETURNING id",
            (point.name, point.mqtt_topic, point.power_w)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return {"id": new_id, "status": "created"}
    except psycopg2.IntegrityError:
        raise HTTPException(status_code=400, detail="MQTT Topic already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        release_db_conn(conn)

@app.delete("/api/config/points/{point_id}")
def delete_point(point_id: int):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM light_points WHERE id = %s", (point_id,))
        conn.commit()
        cur.close()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        release_db_conn(conn)

@app.get("/api/config/solar_history")
def get_solar_history():
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        # Busca acionamentos da última semana filtrando por solar_trigger
        query = """
            SELECT le.timestamp, lp.name, le.event_type 
            FROM light_events le
            JOIN light_points lp ON le.point_id = lp.id
            WHERE le.source = 'solar_trigger' 
            AND le.timestamp > CURRENT_DATE - INTERVAL '7 days'
            ORDER BY le.timestamp DESC
            LIMIT 50;
        """
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        # Formata o timestamp (considerando que o banco já está em America/Sao_Paulo na sessão)
        return [{
            "timestamp": r[0].isoformat() if r[0] else None,
            "name": r[1],
            "event": r[2]
        } for r in rows]
    except Exception as e:
        print(f"Erro Histórico Solar: {e}")
        return []
    finally:
        release_db_conn(conn)

@app.get("/api/sun")
def get_sun_times():
    today = str(date.today())
    if sun_cache["date"] == today: return sun_cache["results"]
    try:
        if os.path.exists(SUN_CACHE_FILE):
            with open(SUN_CACHE_FILE, "r") as f:
                data = json.load(f)
                if data.get("date") == today:
                    sun_cache.update(data)
                    return sun_cache["results"]
                if not sun_cache["results"]: sun_cache.update(data)
    except Exception:
        pass
    try:
        url = f"https://api.sunrise-sunset.org/json?lat={LAT}&lng={LONG}&formatted=0"
        res = requests.get(url, timeout=5).json()
        if res.get("status") == "OK":
            sun_cache.update({"date": today, "results": res["results"]})
            with open(SUN_CACHE_FILE, "w") as f:
                json.dump(sun_cache, f)
            return res["results"]
    except Exception:
        pass
    if sun_cache["results"]: return sun_cache["results"]
    raise HTTPException(status_code=500, detail="Sun data unavailable")

@app.get("/api/status")
def get_status():
    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, mqtt_topic FROM light_points")
        points = cur.fetchall()
        
        results = []
        for p in points:
            results.append({
                "id": p[0],
                "name": p[1],
                "topic": p[2],
                "state": light_states.get(f"{p[2]}/state", "UNKNOWN")
            })
        cur.close()
        return results
    except Exception as e:
        print(f"Erro DB: {e}")
        return []
    finally:
        if conn:
            release_db_conn(conn)

@app.get("/api/history")
def get_history():
    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        query = """
            SELECT DATE(timestamp), SUM(EXTRACT(EPOCH FROM (next_t - timestamp))/3600) as hours
            FROM (
                SELECT timestamp, event_type, 
                LEAD(timestamp) OVER (PARTITION BY point_id ORDER BY timestamp) as next_t
                FROM light_events
            ) t
            WHERE event_type = 'ON' AND timestamp > CURRENT_DATE - INTERVAL '7 days'
            AND next_t IS NOT NULL
            GROUP BY DATE(timestamp) ORDER BY DATE(timestamp) ASC;
        """
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        return [{"date": str(r[0]), "hours": round(float(r[1]), 2)} for r in rows]
    except Exception as e:
        print(f"Erro DB History: {e}")
        return []
    finally:
        if conn:
            release_db_conn(conn)

@app.get("/api/history/consumption")
def get_consumption_history():
    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SET timezone TO 'America/Sao_Paulo';")
        query = """
            SELECT 
                DATE(lc.off_timestamp AT TIME ZONE 'America/Sao_Paulo') AS date_br,
                lp.name,
                SUM(lc.duration_seconds) AS total_seconds,
                SUM(lc.consumption_kwh) AS total_kwh
            FROM light_consumption lc
            JOIN light_points lp ON lc.point_id = lp.id
            WHERE lc.off_timestamp >= (CURRENT_DATE - INTERVAL '7 days') AT TIME ZONE 'America/Sao_Paulo'
            GROUP BY date_br, lp.name
            ORDER BY date_br DESC, lp.name ASC;
        """
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        
        by_date = {}
        for row in rows:
            d_str = str(row[0])
            name = row[1]
            hours = round(float(row[2]) / 3600.0, 2)
            kwh = round(float(row[3]), 4)
            
            if d_str not in by_date:
                by_date[d_str] = []
            by_date[d_str].append({
                "name": name,
                "hours": hours,
                "kwh": kwh
            })
            
        result = []
        for d_str in sorted(by_date.keys(), reverse=True):
            result.append({
                "date": d_str,
                "points": by_date[d_str]
            })
        return result
    except Exception as e:
        print(f"Erro DB History Consumption: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            release_db_conn(conn)

@app.get("/api/consumption/monthly")
def get_monthly_consumption():
    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SET timezone TO 'America/Sao_Paulo';")
        
        # 1. Busca a tarifa base
        tarifa_kwh = 0.0
        dist_name = None
        if DISTRIBUTOR_SLUG:
            cur.execute(
                "SELECT distribuidora, tarifa_energia_kwh, tarifa_uso_kwh FROM energy_tariffs WHERE slug = %s",
                (DISTRIBUTOR_SLUG.lower().strip(),)
            )
            t_res = cur.fetchone()
            if t_res:
                dist_name = t_res[0]
                te = float(t_res[1])
                tusd = float(t_res[2]) if t_res[2] else 0.0
                tarifa_kwh = (te + tusd) * (1.0 + TAX_RATE)
        
        # 2. Busca o consumo do mês atual para cada ponto
        query = """
            SELECT 
                lp.name,
                COALESCE(SUM(lc.consumption_kwh), 0) AS total_kwh,
                COALESCE(SUM(lc.duration_seconds), 0) AS total_seconds
            FROM light_points lp
            LEFT JOIN light_consumption lc ON lc.point_id = lp.id 
              AND lc.off_timestamp >= DATE_TRUNC('month', CURRENT_DATE AT TIME ZONE 'America/Sao_Paulo') AT TIME ZONE 'America/Sao_Paulo'
            GROUP BY lp.name
            ORDER BY lp.name ASC;
        """
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        
        points_data = []
        total_kwh_sum = 0.0
        total_cost_sum = 0.0
        total_hours_sum = 0.0
        
        for name, kwh, seconds in rows:
            kwh_f = float(kwh)
            hours_f = float(seconds) / 3600.0
            cost_f = kwh_f * tarifa_kwh if tarifa_kwh > 0 else 0.0
            
            total_kwh_sum += kwh_f
            total_cost_sum += cost_f
            total_hours_sum += hours_f
            
            points_data.append({
                "name": name,
                "kwh": round(kwh_f, 4),
                "hours": round(hours_f, 2),
                "cost": round(cost_f, 2)
            })
            
        return {
            "distribuidora": dist_name,
            "tarifa_kwh": round(tarifa_kwh, 4),
            "tax_rate": TAX_RATE,
            "total_kwh": round(total_kwh_sum, 4),
            "total_hours": round(total_hours_sum, 2),
            "total_cost": round(total_cost_sum, 2),
            "points": points_data
        }
    except Exception as e:
        print(f"Erro DB Monthly Consumption: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            release_db_conn(conn)

@app.post("/api/command")
def send_command(req: CommandRequest):
    topic_set = f"{req.topic}/set"
    if mqtt_client.is_connected():
        # Registra a persistência de override manual e evento no banco
        conn = get_db_conn()
        try:
            cur = conn.cursor()
            cur.execute("SET timezone TO 'America/Sao_Paulo';")
            # Busca o ID da luz
            cur.execute("SELECT id FROM light_points WHERE mqtt_topic = %s", (req.topic,))
            res = cur.fetchone()
            if res:
                point_id = res[0]
                # Atualiza a coluna manual_override com o novo estado solicitado
                cur.execute(
                    "UPDATE light_points SET manual_override = %s WHERE id = %s",
                    (req.action, point_id)
                )
                # Salva o evento como 'manual_control'
                cur.execute(
                    "INSERT INTO light_events (point_id, event_type, source, timestamp) VALUES (%s, %s, 'manual_control', NOW())",
                    (point_id, req.action)
                )
                conn.commit()
            cur.close()
        except Exception as e:
            if conn: conn.rollback()
            print(f"Erro ao salvar comando manual no banco: {e}")
        finally:
            if conn: release_db_conn(conn)

        # Publica com QoS 1 para garantir a entrega ao broker
        info = mqtt_client.publish(topic_set, req.action, qos=1)
        info.wait_for_publish(timeout=1.0) # Espera confirmação breve
        return {"status": "sent", "topic": topic_set, "action": req.action}
    else:
        raise HTTPException(status_code=503, detail="MQTT Broker offline")

# Configuração dos caminhos de logs com fallback para desenvolvimento local
PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')

LOG_FILES = {
    "api": os.path.join(LOGS_DIR, "api.log"),
    "bot": os.path.join(LOGS_DIR, "bot.log"),
    "solar": os.path.join(LOGS_DIR, "solar.log"),
    "broker": "/var/log/mosquitto/mosquitto.log",
    "devices": os.path.join(LOGS_DIR, "devices.log")
}

# Fallback se o log do broker real não for acessível (ex: local/dev ou permissões)
if not os.path.exists("/var/log/mosquitto/mosquitto.log"):
    mock_broker_path = os.path.join(LOGS_DIR, "mosquitto.log")
    if not os.path.exists(mock_broker_path):
        os.makedirs(LOGS_DIR, exist_ok=True)
        with open(mock_broker_path, "w", encoding="utf-8") as f:
            f.write("[SYSTEM] Simulador de logs do mosquitto ativo localmente...\n")
    LOG_FILES["broker"] = mock_broker_path

async def tail_log_file(file_path: str, last_lines_count: int = 50):
    if not os.path.exists(file_path):
        yield f"data: [ERRO] O arquivo de log '{os.path.basename(file_path)}' não foi encontrado.\n\n"
        return

    # 1. Envia as últimas N linhas de histórico
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            history = lines[-last_lines_count:] if len(lines) > last_lines_count else lines
            for line in history:
                yield f"data: {line.strip()}\n\n"
    except Exception as e:
        yield f"data: [ERRO] Falha ao ler histórico: {str(e)}\n\n"
        return

    # 2. Transmite novas linhas em tempo real (tail -f)
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                yield f"data: {line.strip()}\n\n"
    except asyncio.CancelledError:
        pass
    except Exception as e:
        yield f"data: [ERRO] Erro na transmissão: {str(e)}\n\n"

@app.get("/api/logs/{service}")
async def stream_service_logs(service: str):
    if service not in LOG_FILES:
        raise HTTPException(status_code=400, detail=f"Serviço '{service}' inválido.")
    return StreamingResponse(
        tail_log_file(LOG_FILES[service]),
        media_type="text/event-stream"
    )

@app.get("/api/logs/{service}/download")
def download_service_log(service: str):
    if service not in LOG_FILES:
        raise HTTPException(status_code=400, detail=f"Serviço '{service}' inválido.")
    file_path = LOG_FILES[service]
    if not os.path.exists(file_path):
        if service == "devices":
            return Response(
                content="",
                media_type="text/plain",
                headers={"Content-Disposition": "attachment; filename=devices_log.txt"}
            )
        raise HTTPException(status_code=404, detail="Arquivo de log não encontrado.")
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={service}_log.txt"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler arquivo de log: {e}")

# Serve o frontend
# Usa caminho absoluto baseado no local deste script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
web_path = os.path.join(BASE_DIR, '..', 'web')

if os.path.exists(web_path):
    app.mount("/", StaticFiles(directory=web_path, html=True), name="static")
else:
    print(f"AVISO: Diretorio web nao encontrado em: {web_path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
