import os
import requests
import psycopg2
from psycopg2 import pool
import json
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
import time

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

# Cache de estados
light_states = {}
SUN_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'sun_cache.json')
sun_cache = {"date": None, "results": None}

# MQTT Setup
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def on_connect(client, userdata, flags, rc, properties):
    print(f"Conectado ao MQTT Broker com resultado: {rc}")
    client.subscribe("home/outdoor/+/state")

def on_message(client, userdata, msg):
    topic = msg.topic
    state = msg.payload.decode()
    light_states[topic] = state
    print(f"Estado recebido: {topic} -> {state}")

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

# DB Pooling
db_pool = pool.ThreadedConnectionPool(
    1, 10,
    host=os.getenv("POSTGRES_HOST", "localhost"),
    database=os.getenv("POSTGRES_DB", "light_manager"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD"),
    port=os.getenv("POSTGRES_PORT", "5433")
)

def get_db_conn():
    return db_pool.getconn()

def release_db_conn(conn):
    db_pool.putconn(conn)

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
    conn = get_db_conn()
    try:
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
        release_db_conn(conn)

@app.get("/api/history")
def get_history():
    conn = get_db_conn()
    try:
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
        release_db_conn(conn)

@app.post("/api/command")
def send_command(req: CommandRequest):
    topic_set = f"{req.topic}/set"
    if mqtt_client.is_connected():
        # Publica com QoS 1 para garantir a entrega ao broker
        info = mqtt_client.publish(topic_set, req.action, qos=1)
        info.wait_for_publish(timeout=1.0) # Espera confirmação breve
        return {"status": "sent", "topic": topic_set, "action": req.action}
    else:
        raise HTTPException(status_code=503, detail="MQTT Broker offline")

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
