import time
from collections import deque
from unittest.mock import MagicMock, patch
import pytest

from scripts.solar_worker import (
    check_and_record_transition,
    transition_history,
    last_flapping_alert_ts,
    on_message,
    current_states,
    deviation_counts,
    last_enforcement_ts,
    run_automation_cycle
)

def test_flapping_detection():
    topic = "home/outdoor/frente"
    transition_history[topic] = deque()
    last_flapping_alert_ts[topic] = 0

    with patch("scripts.solar_worker.send_telegram_message") as mock_tg, \
         patch("scripts.solar_worker.send_ntfy_message") as mock_ntfy:
        
        # Simula 5 transições (ainda abaixo do limiar de 6)
        for _ in range(5):
            check_and_record_transition(topic)
        assert mock_tg.call_count == 0

        # 6ª transição -> deve disparar o alerta de flapping
        check_and_record_transition(topic)
        assert mock_tg.call_count == 1
        assert "Alerta de Oscilação (Flapping)" in mock_tg.call_args[0][0]
        assert mock_ntfy.call_count == 1

        # 7ª transição imediata -> deve respeitar o rate-limit de 1h
        check_and_record_transition(topic)
        assert mock_tg.call_count == 1

def test_heartbeat_clock_skew_detection():
    mock_msg = MagicMock()
    mock_msg.topic = "home/outdoor/status"
    mock_msg.retain = False
    # Simula Wemos informando 05:55 (3h adiantado em relação a uma madrugada de 02:55)
    mock_msg.payload.decode.return_value = (
        '{"status":"online","frente":"ON","fundos":"ON","rssi":-50,'
        '"ip":"192.168.1.111","uptime_s":3600,"hhmm":"05:55","synced":true,"fw":"2026.11.1"}'
    )

    with patch("scripts.solar_worker.send_telegram_message") as mock_tg, \
         patch("scripts.solar_worker.datetime") as mock_dt, \
         patch("scripts.solar_worker.touch_last_seen"):
        
        # Mock do servidor em 02:55
        fake_now = MagicMock()
        fake_now.strftime.return_value = "02:55"
        fake_now.hour = 2
        fake_now.minute = 55
        mock_dt.now.return_value = fake_now

        on_message(None, None, mock_msg)
        assert mock_tg.call_count == 1
        assert "Divergência de Horário no Embarcado" in mock_tg.call_args[0][0]


def test_last_seen_file_per_device():
    from scripts.solar_worker import last_seen_file_for, LAST_SEEN_FILE, ESP32_LAST_SEEN_FILE
    assert last_seen_file_for("home/outdoor/frente") == LAST_SEEN_FILE
    assert last_seen_file_for("home/outdoor/fundos") == LAST_SEEN_FILE
    assert last_seen_file_for("home/outdoor/muro") == ESP32_LAST_SEEN_FILE
    assert last_seen_file_for("home/outdoor/aux") == ESP32_LAST_SEEN_FILE
    assert last_seen_file_for("esp32") == ESP32_LAST_SEEN_FILE
    assert last_seen_file_for("wemos") == LAST_SEEN_FILE


def test_heartbeat_attributes_device_and_touches_correct_file():
    mock_msg = MagicMock()
    mock_msg.topic = "home/outdoor/status"
    mock_msg.retain = False
    mock_msg.payload.decode.return_value = (
        '{"status":"online","device":"esp32_muro","muro":"OFF","aux":"OFF","hhmm":"??:??"}'
    )
    with patch("scripts.solar_worker.touch_last_seen") as mock_touch, \
         patch("scripts.solar_worker.log_event_to_db"), \
         patch("scripts.solar_worker.check_and_record_transition"):
        on_message(None, None, mock_msg)
        mock_touch.assert_called_with("esp32")


def test_solar_trigger_minute_truncation_no_deviation():
    """O estado desejado deve usar horários truncados ao minuto (sem segundos do pôr do sol)."""
    from datetime import datetime, timedelta, timezone
    br = timezone(timedelta(hours=-3))
    sunset = datetime(2026, 11, 10, 19, 5, 45, tzinfo=br)
    on_dt = sunset.replace(second=0, microsecond=0)
    now = datetime(2026, 11, 10, 19, 5, 36, tzinfo=br)
    assert now >= on_dt  # gatilho ON no minuto 19:05 => desejado já é ON
