import os
import pytest
from unittest.mock import patch, MagicMock
from scripts.solar_forecast import (
    fetch_solar_forecast,
    calculate_system_efficiency_factor,
    WMO_WEATHER_CODES
)

def test_wmo_weather_codes():
    assert 0 in WMO_WEATHER_CODES
    assert WMO_WEATHER_CODES[0][0] == "Céu Limpo"
    assert WMO_WEATHER_CODES[3][0] == "Nublado"

def test_calculate_system_efficiency_factor_default():
    factor = calculate_system_efficiency_factor(conn=None)
    assert factor == 0.70

@patch("requests.get")
def test_fetch_solar_forecast_success(mock_get, tmp_path):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "daily": {
            "time": ["2026-08-01", "2026-08-02"],
            "shortwave_radiation_sum": [18.0, 15.0],
            "weather_code": [0, 2]
        }
    }
    mock_get.return_value = mock_resp

    res = fetch_solar_forecast(lat=-24.2839, lon=-53.84, force_refresh=True)

    assert res is not None
    assert "today" in res
    assert "tomorrow" in res
    assert res["today"]["date"] == "2026-08-01"
    assert res["today"]["estimated_kwh"] == round(18.0 * 0.70, 2)
    assert res["tomorrow"]["condition"] == "Parcialmente Nublado"
