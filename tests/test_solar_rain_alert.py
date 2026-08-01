import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from scripts.solar_rain_alert import check_abrupt_power_drop_and_rain

BR_TZ = timezone(timedelta(hours=-3))

def test_rain_alert_partial_drop_above_100w():
    # Drop de 1462W para 472W não deve disparar alerta pois potência residual é > 100W
    telemetry = {"power_w": 472.0, "status": "Normal"}
    now_noon = datetime.now(BR_TZ).replace(hour=15, minute=27)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=1462.0, now_obj=now_noon, dry_run=True)
    assert res is False

def test_rain_alert_drop_below_100w():
    # Drop de 1462W para 80W deve disparar alerta pois potência residual é <= 100W
    telemetry = {"power_w": 80.0, "status": "Normal"}
    now_noon = datetime.now(BR_TZ).replace(hour=15, minute=27)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=1462.0, now_obj=now_noon, dry_run=True)
    assert res is True

def test_rain_alert_waiting_status_during_daytime():
    # Entrada em status Waiting durante o dia (14h) deve disparar alerta de chuva
    telemetry = {"power_w": 0.0, "status": "Waiting"}
    now_noon = datetime.now(BR_TZ).replace(hour=14, minute=0)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=1200.0, now_obj=now_noon, dry_run=True)
    assert res is True

def test_rain_alert_outside_peak_hours():
    # Queda ou Waiting fora do horário diurno (ex: 8h ou 17h30) não dispara alerta de chuva
    telemetry = {"power_w": 0.0, "status": "Waiting"}
    now_sunset = datetime.now(BR_TZ).replace(hour=17, minute=30)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=500.0, now_obj=now_sunset, dry_run=True)
    assert res is False
