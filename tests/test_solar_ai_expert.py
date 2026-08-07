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

@patch("scripts.solar_forecast.fetch_solar_forecast", return_value={"today": {"condition_full": "Nublado ☁️"}})
@patch("requests.post")
def test_solar_ai_expert_with_gemini_key_and_weather_correlation(mock_post, mock_forecast):
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

        # Verifica se o payload enviado ao Gemini inclui o contexto climático
        called_json = mock_post.call_args[1]["json"]
        prompt_parts = called_json["contents"][0]["parts"]
        system_prompt = prompt_parts[0]["text"]
        user_prompt = prompt_parts[1]["text"]

        assert "GUARDRAILS CLIMÁTICOS E OPERACIONAIS OBRIGATÓRIOS" in system_prompt
        assert "NUNCA oriente a chamar suporte técnico" in system_prompt
        assert "CONDIÇÃO CLIMÁTICA ATUAL NO LOCAL" in user_prompt
        assert "Nublado ☁️" in user_prompt
