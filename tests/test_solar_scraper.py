import pytest
from unittest.mock import MagicMock, patch
import requests
from scripts.solar_scraper import (
    parse_solar_csv,
    fetch_solar_telemetry,
    save_solar_telemetry,
    publish_solar_mqtt,
    run_solar_scraping_cycle
)

SAMPLE_CSV = "1,1692894,180154,1048,64,1304,788,1953,610,65535,65535,0,0,65535,65535,0,0,65535,65535,0,0,65535,65535,2146,6000,2282,923,65535,65535,65535,65535,3649,432,132892,2"

def test_parse_solar_csv_success():
    res = parse_solar_csv(SAMPLE_CSV)
    assert res["total_kwh"] == 16928.94
    assert res["total_hours"] == 18015.4
    assert res["today_kwh"] == 10.48
    assert res["today_hours"] == 6.4
    assert res["pv1_voltage"] == 130.4
    assert res["pv1_current"] == 7.88
    assert res["pv2_voltage"] == 195.3
    assert res["pv2_current"] == 6.10
    assert res["power_w"] == 2146.0
    assert res["grid_frequency"] == 60.0
    assert res["grid_voltage"] == 228.2
    assert res["grid_current"] == 9.23
    assert res["bus_voltage"] == 364.9
    assert res["temperature"] == 43.2
    assert res["co2_reduction_kg"] == 13289.2
    assert res["state_code"] == 2
    assert res["status"] == "Normal"

def test_parse_solar_csv_invalid_length():
    with pytest.raises(ValueError):
        parse_solar_csv("1,2,3")

@patch("requests.post")
def test_fetch_solar_telemetry_online(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_CSV
    mock_post.return_value = mock_resp

    res = fetch_solar_telemetry(ip="192.168.1.13")
    assert res is not None
    assert res["power_w"] == 2146.0
    assert res["status"] == "Normal"

@patch("requests.post")
def test_fetch_solar_telemetry_offline(mock_post):
    mock_post.side_effect = requests.exceptions.ConnectTimeout("Connection timed out")
    res = fetch_solar_telemetry(ip="192.168.1.13")
    assert res is None

def test_publish_solar_mqtt_online():
    mock_mqtt = MagicMock()
    telemetry = {
        "power_w": 2000.0,
        "today_kwh": 12.5,
        "status": "Normal"
    }
    publish_solar_mqtt(telemetry, mock_mqtt)
    assert mock_mqtt.publish.call_count == 4
    topics = [call[0][0] for call in mock_mqtt.publish.call_args_list]
    assert "home/solar/telemetry" in topics
    assert "home/solar/power_w" in topics
    assert "home/solar/today_kwh" in topics
    assert "home/solar/status" in topics

def test_publish_solar_mqtt_offline():
    mock_mqtt = MagicMock()
    publish_solar_mqtt(None, mock_mqtt)
    assert mock_mqtt.publish.call_count == 2
    topics = [call[0][0] for call in mock_mqtt.publish.call_args_list]
    assert "home/solar/status" in topics
    assert "home/solar/power_w" in topics
