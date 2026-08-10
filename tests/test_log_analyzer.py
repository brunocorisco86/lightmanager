# tests/test_log_analyzer.py
import pytest
from unittest.mock import patch, MagicMock
from scripts.log_analyzer import get_weather_and_solar_context, extract_errors, main

def test_get_weather_and_solar_context():
    mock_forecast = {
        "today": {
            "condition": "Chuva Moderada",
            "condition_full": "Chuva Moderada 🌧️",
            "estimated_kwh": 3.5
        }
    }
    with patch("scripts.solar_forecast.fetch_solar_forecast", return_value=mock_forecast):
        ctx = get_weather_and_solar_context()
        assert "condition" in ctx
        assert "estimated_kwh" in ctx
        assert "is_solar_window" in ctx

def test_solar_standby_guardrail_filters_404(tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    solar_log = logs_dir / "solar.log"
    solar_log.write_text("2026-08-10 19:00:00 - ERROR - Inversor solar (192.168.1.13) retornou código HTTP 404\n")

    mock_weather = {
        "condition": "Chuva Moderada 🌧️",
        "estimated_kwh": 0.5,
        "is_solar_window": False, # Horário noturno/pós-pôr do sol
        "detail": "Clima Hoje: Chuva Moderada"
    }

    with patch("scripts.log_analyzer.LOGS_DIR", str(logs_dir)), \
         patch("scripts.log_analyzer.LOG_FILES", {"solar": str(solar_log)}), \
         patch("scripts.log_analyzer.get_weather_and_solar_context", return_value=mock_weather), \
         patch("scripts.log_analyzer.send_telegram_message") as mock_tg:
        
        main()
        # Como o erro 404 foi ignorado pelo guardrail noturno/chuva, o status deve ser "Tudo OK"
        mock_tg.assert_called_once()
        msg_text = mock_tg.call_args[0][0]
        assert "Tudo OK" in msg_text

def test_extract_errors_ignores_self_logs(tmp_path):
    cron_log = tmp_path / "cron.log"
    cron_log.write_text(
        "[2026-08-10 19:00:02] Iniciando monitoramento de logs diários...\n"
        "Detectados 1 tipos de erros consolidados. Solicitando resumo à IA...\n"
        "Enviando relatório via Telegram...\n"
    )
    with patch("scripts.log_analyzer.LOG_FILES", {"cron": str(cron_log)}):
        errs = extract_errors()
        assert len(errs) == 0

