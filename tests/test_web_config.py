import os
import pytest
import psycopg2
from fastapi.testclient import TestClient
from web_api.main import app

client = TestClient(app)

# Helper para limpar dados de teste
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "light_manager"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", "5433")
    )

@pytest.fixture(autouse=True)
def setup_db():
    # Limpa dados de teste antes de cada execução
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM light_events WHERE source = 'test_trigger'")
    cur.execute("DELETE FROM light_points WHERE mqtt_topic LIKE 'home/test/%'")
    conn.commit()
    cur.close()
    conn.close()

def test_config_points_crud():
    # 1. Testar Cadastro (POST)
    payload = {
        "name": "Test Point",
        "mqtt_topic": "home/test/point1",
        "power_w": 50.5
    }
    response = client.post("/api/config/points", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    point_id = data["id"]

    # 2. Testar Listagem (GET)
    response = client.get("/api/config/points")
    assert response.status_code == 200
    points = response.json()
    assert any(p["id"] == point_id for p in points)

    # 3. Testar Atualização (PUT)
    update_payload = {
        "offset_on_minutes": 10,
        "offset_off_minutes": -20
    }
    response = client.put(f"/api/config/points/{point_id}", json=update_payload)
    assert response.status_code == 200

    # Verificar se atualizou
    response = client.get("/api/config/points")
    point = next(p for p in response.json() if p["id"] == point_id)
    assert point["offset_on"] == 10
    assert point["offset_off"] == -20
    assert point["trigger_mode"] == "solar"
    assert point["auto_mode"] is True

    # 4. Testar Mudança para Regra de Câmeras NVR (trigger_mode='camera')
    cam_update = {
        "offset_on_minutes": 0,
        "offset_off_minutes": 0,
        "trigger_mode": "camera",
        "camera_channels": "3,4",
        "camera_hold_seconds": 120,
        "camera_night_only": True
    }
    response = client.put(f"/api/config/points/{point_id}", json=cam_update)
    assert response.status_code == 200

    response = client.get("/api/config/points")
    point = next(p for p in response.json() if p["id"] == point_id)
    assert point["trigger_mode"] == "camera"
    assert point["camera_channels"] == "3,4"
    assert point["camera_hold_seconds"] == 120
    assert point["camera_night_only"] is True
    assert point["auto_mode"] is False


def test_nvr_channels_endpoint():
    response = client.get("/api/nvr/channels")
    assert response.status_code == 200
    channels = response.json()
    assert isinstance(channels, list)
    assert len(channels) == 9
    assert any(c["code"] == "D03" for c in channels)
    assert any(c["code"] == "D04" for c in channels)

def test_solar_history_endpoint():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Inserir um ponto e um evento de teste
    cur.execute(
        "INSERT INTO light_points (name, mqtt_topic, power_w) VALUES (%s, %s, %s) RETURNING id",
        ("History Test", "home/test/history", 10)
    )
    p_id = cur.fetchone()[0]
    
    # Inserir evento com source 'solar_trigger'
    cur.execute(
        "INSERT INTO light_events (point_id, event_type, source) VALUES (%s, %s, %s)",
        (p_id, "ON", "solar_trigger")
    )
    conn.commit()
    cur.close()
    conn.close()

    # Testar endpoint
    response = client.get("/api/config/solar_history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) > 0
    assert history[0]["name"] == "History Test"
    assert history[0]["event"] == "ON"
