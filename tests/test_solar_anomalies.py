import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from scripts.solar_scraper import check_solar_anomalies

BR_TZ = timezone(timedelta(hours=-3))

def test_check_solar_anomalies_normal():
    telemetry = {
        "status": "Normal",
        "temperature": 38.5,
        "pv1_voltage": 110.0,
        "pv2_voltage": 105.0,
        "power_w": 1800.0
    }
    anomalies = check_solar_anomalies(telemetry, dry_run=True)
    assert len(anomalies) == 0

def test_check_solar_anomalies_high_temperature():
    telemetry = {
        "status": "Normal",
        "temperature": 63.5,
        "pv1_voltage": 110.0,
        "pv2_voltage": 105.0,
        "power_w": 2100.0
    }
    anomalies = check_solar_anomalies(telemetry, dry_run=True)
    assert len(anomalies) == 1
    assert anomalies[0]["key"] == "high_temperature"

def test_check_solar_anomalies_pv_asymmetry():
    now_noon = datetime.now(BR_TZ).replace(hour=12, minute=30)
    telemetry = {
        "status": "Normal",
        "temperature": 40.0,
        "pv1_voltage": 120.0,
        "pv2_voltage": 5.0,
        "power_w": 900.0
    }
    anomalies = check_solar_anomalies(telemetry, now_obj=now_noon, dry_run=True)
    assert len(anomalies) == 1
    assert anomalies[0]["key"] == "pv_string_fault"

def test_check_solar_anomalies_inverter_fault():
    telemetry = {
        "status": "Error",
        "temperature": 35.0,
        "pv1_voltage": 0.0,
        "pv2_voltage": 0.0,
        "power_w": 0.0
    }
    anomalies = check_solar_anomalies(telemetry, dry_run=True)
    assert len(anomalies) == 1
    assert anomalies[0]["key"] == "inverter_fault"
