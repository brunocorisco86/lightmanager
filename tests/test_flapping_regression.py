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


def _setup_nvr_mock_db(mock_get_conn, channels="3,4"):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.return_value = [
        (32, "Muro", "home/outdoor/muro", channels, 120, True)
    ]
    return mock_conn, mock_cur


def test_presence_transient_vehicle_pulse_ignored():
    """Um carro ou moto veloz dispara apenas 1 pulso rápido (< 2s) -> relé NÃO liga."""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "OFF"
    sw.active_camera_timers.clear()
    sw.pending_presence.clear()
    sw.camera_cooldowns.clear()
    sw.continuous_on_tracker.clear()

    client = MagicMock()
    alarm_pkt = {"AlarmInfo": {"Channel": 2, "Status": "Start"}}  # D03

    with patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True), \
         patch("time.time", return_value=2000.0):
        _setup_nvr_mock_db(mock_conn)
        sw.process_nvr_alarm_packet(client, alarm_pkt)

        # Relé não deve ser acionado
        client.publish.assert_not_called()
        assert sw.current_states["home/outdoor/muro"] == "OFF"
        assert "home/outdoor/muro" in sw.pending_presence
        assert sw.pending_presence["home/outdoor/muro"]["first_ts"] == 2000.0


def test_presence_sustained_human_walkby_confirms_and_activates():
    """Dois pulsos espaçados entre 2.0s e 7.0s (pedestre caminhando) -> confirma e liga relé."""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "OFF"
    sw.active_camera_timers.clear()
    sw.pending_presence.clear()
    sw.camera_cooldowns.clear()
    sw.continuous_on_tracker.clear()

    client = MagicMock()
    alarm_pkt = {"AlarmInfo": {"Channel": 2, "Status": "Start"}}  # D03

    with patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True), \
         patch("scripts.solar_worker.log_event_to_db"):
        _setup_nvr_mock_db(mock_conn)

        # 1º pulso (t=2000.0) -> probation
        with patch("time.time", return_value=2000.0):
            sw.process_nvr_alarm_packet(client, alarm_pkt)
            client.publish.assert_not_called()

        # 2º pulso (t=2002.5 -> dt=2.5s) -> confirmação de presença!
        with patch("time.time", return_value=2002.5):
            sw.process_nvr_alarm_packet(client, alarm_pkt)
            client.publish.assert_called_with("home/outdoor/muro/set", "ON", qos=1, retain=True)
            assert sw.current_states["home/outdoor/muro"] == "ON"
            assert "home/outdoor/muro" not in sw.pending_presence
            assert sw.active_camera_timers["home/outdoor/muro"] == 2002.5 + 120


def test_presence_cross_camera_correlation_confirms_immediately():
    """Câmeras diferentes vinculadas (D03 e D04) detectando dentro da janela confirmam imediatamente."""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "OFF"
    sw.active_camera_timers.clear()
    sw.pending_presence.clear()
    sw.camera_cooldowns.clear()
    sw.continuous_on_tracker.clear()

    client = MagicMock()
    pkt_d03 = {"AlarmInfo": {"Channel": 2, "Status": "Start"}}  # D03 (idx 2)
    pkt_d04 = {"AlarmInfo": {"Channel": 3, "Status": "Start"}}  # D04 (idx 3)

    with patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True), \
         patch("scripts.solar_worker.log_event_to_db"):
        _setup_nvr_mock_db(mock_conn, channels="3,4")

        # 1º pulso na D03 em t=3000.0
        with patch("time.time", return_value=3000.0):
            sw.process_nvr_alarm_packet(client, pkt_d03)
            client.publish.assert_not_called()

        # 2º pulso na D04 logo em seguida (t=3000.8 -> dt=0.8s) -> correlação multi-câmera confirma!
        with patch("time.time", return_value=3000.8):
            sw.process_nvr_alarm_packet(client, pkt_d04)
            client.publish.assert_called_with("home/outdoor/muro/set", "ON", qos=1, retain=True)
            assert sw.current_states["home/outdoor/muro"] == "ON"


def test_presence_cooldown_anti_flippering():
    """Após desligamento por timeout, novo alarme durante cooldown de 15s é ignorado."""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "ON"
    sw.active_camera_timers["home/outdoor/muro"] = 4000.0
    sw.camera_cooldowns.clear()
    sw.pending_presence.clear()

    client = MagicMock()
    alarm_pkt = {"AlarmInfo": {"Channel": 2, "Status": "Start"}}

    with patch("scripts.solar_worker.log_event_to_db"), \
         patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True):
        _setup_nvr_mock_db(mock_conn)

        # Timeout aos 4000.0s -> desliga e entra em cooldown de 15s (até 4015.0)
        sw.check_expired_camera_timers(client, now_ts=4000.0)
        client.publish.assert_called_with("home/outdoor/muro/set", "OFF", qos=1, retain=True)
        assert sw.current_states["home/outdoor/muro"] == "OFF"
        assert sw.camera_cooldowns["home/outdoor/muro"] == 4015.0

        # Alarme aos 4008.0s (durante cooldown de 15s) -> IGNORADO
        client.publish.reset_mock()
        with patch("time.time", return_value=4008.0):
            sw.process_nvr_alarm_packet(client, alarm_pkt)
            client.publish.assert_not_called()
            assert sw.current_states["home/outdoor/muro"] == "OFF"


def test_presence_continuous_ceiling_stops_renewal():
    """Se a lâmpada ficar 300s ininterruptos ligada, novos alarmes não renovam o timer."""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "ON"
    sw.active_camera_timers["home/outdoor/muro"] = 5120.0
    sw.continuous_on_tracker["home/outdoor/muro"] = 5000.0  # Ligou em 5000.0

    client = MagicMock()
    alarm_pkt = {"AlarmInfo": {"Channel": 2, "Status": "Start"}}

    with patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True):
        _setup_nvr_mock_db(mock_conn)

        # Alarme em t=5305.0 (305s contínuos >= 300s teto máximo)
        with patch("time.time", return_value=5305.0):
            sw.process_nvr_alarm_packet(client, alarm_pkt)
            # O timer NÃO deve ser renovado (permanece 5120.0)
            assert sw.active_camera_timers["home/outdoor/muro"] == 5120.0
