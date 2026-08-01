import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from scripts.solar_rain_alert import check_abrupt_power_drop_and_rain

BR_TZ = timezone(timedelta(hours=-3))

def test_rain_alert_normal_power_change():
    telemetry = {"power_w": 2000.0}
    now_noon = datetime.now(BR_TZ).replace(hour=14, minute=0)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=2100.0, now_obj=now_noon, dry_run=True)
    assert res is False

def test_rain_alert_abrupt_drop_peak_hours():
    telemetry = {"power_w": 350.0}
    now_noon = datetime.now(BR_TZ).replace(hour=14, minute=0)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=2200.0, now_obj=now_noon, dry_run=True)
    assert res is True

def test_rain_alert_outside_peak_hours():
    telemetry = {"power_w": 350.0}
    now_night = datetime.now(BR_TZ).replace(hour=8, minute=0)
    res = check_abrupt_power_drop_and_rain(telemetry, previous_power_w=2200.0, now_obj=now_night, dry_run=True)
    assert res is False
