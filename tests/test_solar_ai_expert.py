import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from scripts.solar_ai_expert import analyze_solar_anomaly_with_ai

BR_TZ = timezone(timedelta(hours=-3))

def test_solar_ai_expert_no_key():
    with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
        anomaly = {"title": "Sobretemperatura Crítica", "detail": "Temp 63.5 °C"}
        telemetry = {"power_w": 2000, "temperature": 63.5, "status": "Normal"}
        res = analyze_solar_anomaly_with_ai(anomaly, telemetry, dry_run=True)
        assert "GEMINI_API_KEY" in res
        assert "não está configurada" in res

@patch("requests.post")
def test_solar_ai_expert_with_gemini_key(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": "🧠 *Diagnóstico da Causa Raiz*\nSuperaquecimento do inversor devido a ventilação obstruída."
                }]
            }
        }]
    }
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key_12345"}, clear=False):
        anomaly = {"title": "Sobretemperatura Crítica", "detail": "Temp 63.5 °C"}
        telemetry = {"power_w": 2000, "temperature": 63.5, "status": "Normal"}
        res = analyze_solar_anomaly_with_ai(anomaly, telemetry, dry_run=True)
        assert "Superaquecimento do inversor" in res
