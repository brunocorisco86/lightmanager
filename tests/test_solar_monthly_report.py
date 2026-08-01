import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from scripts.solar_monthly_report import (
    get_target_month_range,
    render_monthly_chart,
    generate_ai_monthly_consultant_report,
    run_monthly_report_flow
)

BR_TZ = timezone(timedelta(hours=-3))

def test_get_target_month_range():
    # Testando com data em Agosto de 2026 -> Mês anterior deve ser Julho de 2026 (31 dias)
    now_aug = datetime(2026, 8, 15, 10, 0, tzinfo=BR_TZ)
    year, month, month_name, days_in_month = get_target_month_range(now_aug)
    assert year == 2026
    assert month == 7
    assert month_name == "Julho"
    assert days_in_month == 31

def test_get_target_month_range_january():
    # Testando virada de ano em Janeiro de 2027 -> Mês anterior deve ser Dezembro de 2026 (31 dias)
    now_jan = datetime(2027, 1, 10, 10, 0, tzinfo=BR_TZ)
    year, month, month_name, days_in_month = get_target_month_range(now_jan)
    assert year == 2026
    assert month == 12
    assert month_name == "Dezembro"
    assert days_in_month == 31

def test_render_monthly_chart():
    daily_data = {d: {"kwh": float(d * 0.5), "max_w": 1500.0, "avg_temp": 35.0} for d in range(1, 31)}
    chart_path = render_monthly_chart(2026, 7, "Julho", daily_data)
    assert os.path.exists(chart_path)
    assert os.path.getsize(chart_path) > 0
    if os.path.exists(chart_path):
        os.remove(chart_path)

@patch("requests.post")
def test_generate_ai_monthly_consultant_report_mocked(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": "📊 *Desempenho Geral*\nA usina produziu 350.0 kWh com excelente payback."
                }]
            }
        }]
    }
    mock_post.return_value = mock_resp

    summary_data = {
        "year": 2026,
        "month": 7,
        "month_name": "Julho",
        "days_in_month": 31,
        "total_kwh": 350.0,
        "avg_kwh": 11.29,
        "active_days": 31,
        "peak_w": 2100.0,
        "best_day": 15,
        "best_kwh": 18.5,
        "worst_day": 3,
        "worst_kwh": 4.2,
        "tariff_rate": 1.06,
        "savings_brl": 371.0
    }

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key_123"}, clear=False):
        res = generate_ai_monthly_consultant_report(summary_data)
        assert "Desempenho Geral" in res

def test_run_monthly_report_flow_test_mode():
    now_dt = datetime.now(BR_TZ)
    summary_data, chart_path, ai_report, success = run_monthly_report_flow(dry_run=True, test_mode=True)
    assert summary_data["year"] == now_dt.year
    assert summary_data["month"] == now_dt.month
    assert success is True
    if os.path.exists(chart_path):
        os.remove(chart_path)

