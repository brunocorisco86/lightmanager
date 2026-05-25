import os
import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from fastapi.testclient import TestClient
from datetime import date

# Load test environment variables before anything else
from dotenv import load_dotenv
load_dotenv('.env.test', override=True)

# Mock paho-mqtt to prevent connection attempts during import
with patch('paho.mqtt.client.Client'):
    from web_api.main import app, mqtt_client

client = TestClient(app)

# --- /api/sun tests ---

@patch('requests.get')
@patch('os.path.exists')
@patch('builtins.open', new_callable=mock_open)
def test_get_sun_times_success(mock_file, mock_exists, mock_get):
    # Mock file not exists (no cache)
    mock_exists.return_value = False

    # Mock API response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "OK",
        "results": {
            "sunrise": "2023-10-27T10:00:00+00:00",
            "sunset": "2023-10-27T22:00:00+00:00"
        }
    }
    mock_get.return_value = mock_response

    response = client.get("/api/sun")
    assert response.status_code == 200
    assert response.json()["sunrise"] == "2023-10-27T10:00:00+00:00"
    mock_get.assert_called_once()

@patch('os.path.exists')
@patch('builtins.open', new_callable=mock_open, read_data='{"date": "2023-10-27", "results": {"sunrise": "cached"}}')
def test_get_sun_times_cached(mock_file, mock_exists):
    # Mock date to match cache
    with patch('web_api.main.date') as mock_date:
        mock_date.today.return_value = date(2023, 10, 27)
        mock_exists.return_value = True

        response = client.get("/api/sun")
        assert response.status_code == 200
        assert response.json()["sunrise"] == "cached"

def test_get_sun_times_failure():
    with patch('requests.get', side_effect=Exception("API Down")):
        with patch('web_api.main.sun_cache', {"date": None, "results": None}):
             with patch('os.path.exists', return_value=False):
                response = client.get("/api/sun")
                assert response.status_code == 500
                assert response.json()["detail"] == "Sun data unavailable"

# --- /api/status tests ---

@patch('web_api.main.get_db_conn')
def test_get_status_success(mock_get_conn):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur

    # Mock DB data: (id, name, mqtt_topic)
    mock_cur.fetchall.return_value = [
        (1, "Garden", "home/outdoor/garden"),
        (2, "Pool", "home/outdoor/pool")
    ]

    # Mock light_states
    with patch('web_api.main.light_states', {"home/outdoor/garden/state": "ON"}):
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Garden"
        assert data[0]["state"] == "ON"
        assert data[1]["name"] == "Pool"
        assert data[1]["state"] == "UNKNOWN"

@patch('web_api.main.get_db_conn', side_effect=Exception("DB Connection Error"))
def test_get_status_db_error(mock_get_conn):
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json() == []

# --- /api/history tests ---

@patch('web_api.main.get_db_conn')
def test_get_history_success(mock_get_conn):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur

    # Mock DB data: (date, hours)
    mock_cur.fetchall.return_value = [
        (date(2023, 10, 25), 2.5),
        (date(2023, 10, 26), 3.1)
    ]

    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["date"] == "2023-10-25"
    assert data[0]["hours"] == 2.5

# --- /api/command tests ---

def test_send_command_success():
    mqtt_client.is_connected.return_value = True

    payload = {"topic": "home/outdoor/garden", "action": "ON"}
    response = client.post("/api/command", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "sent"
    mqtt_client.publish.assert_called_with("home/outdoor/garden/set", "ON")

def test_send_command_mqtt_offline():
    mqtt_client.is_connected.return_value = False

    payload = {"topic": "home/outdoor/garden", "action": "OFF"}
    response = client.post("/api/command", json=payload)

    assert response.status_code == 503
    assert response.json()["detail"] == "MQTT Broker offline"
