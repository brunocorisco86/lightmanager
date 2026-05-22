import os
import requests
import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from fastapi.middleware.cors import CORSMiddleware

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
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
LAT = os.getenv("LATITUDE", "0")
LONG = os.getenv("LONGITUDE", "0")

# Cache de estados (em memória para ser rápido)
light_states = {}

# MQTT Setup
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def on_connect(client, userdata, flags, rc, properties):
    client.subscribe("home/outdoor/+/state")

def on_message(client, userdata, msg):
    topic = msg.topic
    state = msg.payload.decode()
    light_states[topic] = state

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# DB Helper
def get_db_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "light_manager"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "secret")
    )

class CommandRequest(BaseModel):
    topic: str
    action: str

@app.get("/api/sun")
def get_sun_times():
    try:
        url = f"https://api.sunrise-sunset.org/json?lat={LAT}&lng={LONG}&formatted=0"
        res = requests.get(url).json()
        return res["results"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
def get_status():
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
    conn.close()
    return results

@app.get("/api/history")
def get_history():
    conn = get_db_conn()
    cur = conn.cursor()
    # Puxa o consumo dos últimos 7 dias
    query = """
        SELECT DATE(timestamp), SUM(EXTRACT(EPOCH FROM (next_t - timestamp))/3600) as hours
        FROM (
            SELECT timestamp, event_type, 
            LEAD(timestamp) OVER (PARTITION BY point_id ORDER BY timestamp) as next_t
            FROM light_events
        ) t
        WHERE event_type = 'ON' AND timestamp > CURRENT_DATE - INTERVAL '7 days'
        GROUP BY DATE(timestamp) ORDER BY DATE(timestamp) ASC;
    """
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"date": str(r[0]), "hours": round(float(r[1]), 2)} for r in rows]

@app.post("/api/command")
def send_command(req: CommandRequest):
    topic_set = f"{req.topic}/set"
    mqtt_client.publish(topic_set, req.action)
    return {"status": "sent", "topic": topic_set, "action": req.action}

# Serve o frontend
app.mount("/", StaticFiles(directory="../web", html=True), name="static")
