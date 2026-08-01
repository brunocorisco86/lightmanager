import os
import pytest
from datetime import datetime, date, timezone, timedelta
from unittest.mock import MagicMock, patch
from scripts.solar_report import (
    calculate_daily_summary,
    generate_solar_chart_png,
    send_daily_solar_telegram_report
)

BR_TZ = timezone(timedelta(hours=-3))

def test_calculate_daily_summary():
    now_br = datetime.now(BR_TZ)
    records = [
        {
            "timestamp": now_br - timedelta(hours=2),
            "power_w": 500.0,
            "today_kwh": 2.5,
            "temperature": 35.0
        },
        {
            "timestamp": now_br - timedelta(hours=1),
            "power_w": 2200.0,
            "today_kwh": 6.8,
            "temperature": 42.5
        },
        {
            "timestamp": now_br,
            "power_w": 1800.0,
            "today_kwh": 10.5,
            "temperature": 40.0
        }
    ]

    summary = calculate_daily_summary(records, target_date=now_br.date())
    assert summary["today_kwh"] == 10.5
    assert summary["peak_power_w"] == 2200.0
    assert summary["max_temp"] == 42.5
    assert summary["record_count"] == 3

def test_generate_solar_chart_png(tmp_path):
    now_br = datetime.now(BR_TZ)
    records = [
        {
            "timestamp": now_br - timedelta(hours=3),
            "power_w": 300.0,
            "today_kwh": 1.0,
            "temperature": 30.0
        },
        {
            "timestamp": now_br - timedelta(hours=2),
            "power_w": 1500.0,
            "today_kwh": 4.0,
            "temperature": 38.0
        },
        {
            "timestamp": now_br - timedelta(hours=1),
            "power_w": 2500.0,
            "today_kwh": 8.5,
            "temperature": 44.0
        }
    ]
    summary = calculate_daily_summary(records, target_date=now_br.date())
    out_file = str(tmp_path / "test_solar_chart.png")

    result_path = generate_solar_chart_png(records, summary, output_path=out_file)
    assert result_path == out_file
    assert os.path.exists(out_file)
    assert os.path.getsize(out_file) > 1000 # O arquivo PNG foi gerado com conteúdo gráfico

@patch("scripts.solar_report.fetch_daily_solar_data")
def test_send_daily_solar_telegram_report_dry_run(mock_fetch, tmp_path):
    now_br = datetime.now(BR_TZ)
    mock_fetch.return_value = [
        {
            "timestamp": now_br,
            "power_w": 1200.0,
            "today_kwh": 5.0,
            "temperature": 36.0
        }
    ]

    res = send_daily_solar_telegram_report(target_date=now_br.date(), dry_run=True)
    assert res is True
