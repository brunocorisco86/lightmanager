import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from scripts.solar_rain_alert import check_abrupt_power_drop_and_rain

BR_TZ = timezone(timedelta(hours=-3))

MOCK_FORECAST = {
    "today": {
        "weather_code": 61,
        "condition": "Chuva Fraca",
        "condition_full": "Chuva Fraca 🌧️"
    }
}

@patch("scripts.solar_forecast.fetch_solar_forecast", return_value=MOCK_FORECAST)
def test_rain_alert_partial_drop_above_100w(mock_fc):
    # Drop de 1462W para 472W não deve disparar alerta pois potência residual é > 120W
    telemetry = {"power_w": 472.0, "status": "Normal"}
    now_noon = datetime.now(BR_TZ).replace(hour=15, minute=27)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=1462.0, now_obj=now_noon, dry_run=True)
    assert res is False

@patch("scripts.solar_forecast.fetch_solar_forecast", return_value=MOCK_FORECAST)
def test_rain_alert_drop_below_100w(mock_fc):
    # Drop de 1462W para 80W deve disparar alerta pois potência residual é <= 120W
    telemetry = {"power_w": 80.0, "status": "Normal"}
    now_noon = datetime.now(BR_TZ).replace(hour=15, minute=27)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=1462.0, now_obj=now_noon, dry_run=True)
    assert res is True

@patch("scripts.solar_forecast.fetch_solar_forecast", return_value=MOCK_FORECAST)
def test_rain_alert_gradual_window_drop(mock_fc):
    # Drop progressivo em 15 min de 610W para 90W (como ocorrido ontem) deve disparar alerta de chuva
    telemetry = {"power_w": 90.0, "status": "Normal"}
    now_afternoon = datetime.now(BR_TZ).replace(hour=15, minute=10)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=610.0, now_obj=now_afternoon, dry_run=True)
    assert res is True

@patch("scripts.solar_forecast.fetch_solar_forecast", return_value=MOCK_FORECAST)
def test_rain_alert_morning_extended_hours(mock_fc):
    # Queda de geração pela manhã (08:30) com tempestade de início de dia deve ser detectada
    telemetry = {"power_w": 50.0, "status": "Normal"}
    now_morning = datetime.now(BR_TZ).replace(hour=8, minute=30)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=450.0, now_obj=now_morning, dry_run=True)
    assert res is True

@patch("scripts.solar_forecast.fetch_solar_forecast", return_value=MOCK_FORECAST)
def test_rain_alert_waiting_status_during_daytime(mock_fc):
    # Entrada em status Waiting durante o dia (14h) deve disparar alerta de chuva
    telemetry = {"power_w": 0.0, "status": "Waiting"}
    now_noon = datetime.now(BR_TZ).replace(hour=14, minute=0)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=1200.0, now_obj=now_noon, dry_run=True)
    assert res is True

@patch("scripts.solar_forecast.fetch_solar_forecast", return_value=MOCK_FORECAST)
def test_rain_alert_outside_peak_hours(mock_fc):
    # Queda ou Waiting fora do horário diurno (ex: 17h45 ou 06h00) não dispara alerta de chuva
    telemetry = {"power_w": 0.0, "status": "Waiting"}
    now_sunset = datetime.now(BR_TZ).replace(hour=17, minute=45)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=500.0, now_obj=now_sunset, dry_run=True)
    assert res is False
