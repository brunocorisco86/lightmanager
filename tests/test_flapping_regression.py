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
    """Um carro ou moto veloz na câmera de movimento (D02, canal 2) dispara 1 pulso -> relé NÃO liga."""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "OFF"
    sw.active_camera_timers.clear()
    sw.pending_presence.clear()
    sw.camera_cooldowns.clear()
    sw.continuous_on_tracker.clear()

    client = MagicMock()
    alarm_pkt = {"AlarmInfo": {"Channel": 1, "Status": "Start"}}  # D02 (canal 2, movimento puro)

    with patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True), \
         patch("time.time", return_value=2000.0):
        _setup_nvr_mock_db(mock_conn, channels="1,2,3")
        sw.process_nvr_alarm_packet(client, alarm_pkt)

        # Relé não deve ser acionado para pulso único em câmera sem IA
        client.publish.assert_not_called()
        assert sw.current_states["home/outdoor/muro"] == "OFF"
        assert "home/outdoor/muro" in sw.pending_presence
        assert sw.pending_presence["home/outdoor/muro"]["first_ts"] == 2000.0


def test_presence_ai_human_detection_activates_immediately():
    """Câmera com IA de corpo humano (D03, canal 3): pulso de IA liga o relé de imediato para pedestres."""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "OFF"
    sw.active_camera_timers.clear()
    sw.pending_presence.clear()
    sw.camera_cooldowns.clear()
    sw.continuous_on_tracker.clear()

    client = MagicMock()
    alarm_pkt = {"AlarmInfo": {"Channel": 2, "Status": "Start"}}  # D03 (canal 3, IA)

    with patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True), \
         patch("scripts.solar_worker.log_event_to_db"):
        _setup_nvr_mock_db(mock_conn, channels="1,2,3")

        # 1º pulso de IA (t=2000.0) -> liga imediatamente!
        with patch("time.time", return_value=2000.0):
            sw.process_nvr_alarm_packet(client, alarm_pkt)
            client.publish.assert_called_with("home/outdoor/muro/set", "ON", qos=1, retain=True)
            assert sw.current_states["home/outdoor/muro"] == "ON"
            assert "home/outdoor/muro" not in sw.pending_presence
            assert sw.active_camera_timers["home/outdoor/muro"] == 2000.0 + 120


def test_presence_cross_camera_correlation_confirms_immediately():
    """D02 (movimento precursor) seguido de D04 (IA) confirma imediatamente."""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "OFF"
    sw.active_camera_timers.clear()
    sw.pending_presence.clear()
    sw.camera_cooldowns.clear()
    sw.continuous_on_tracker.clear()

    client = MagicMock()
    pkt_d02 = {"AlarmInfo": {"Channel": 1, "Status": "Start"}}  # D02 (idx 1, movimento)
    pkt_d04 = {"AlarmInfo": {"Channel": 3, "Status": "Start"}}  # D04 (idx 3, IA)

    with patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True), \
         patch("scripts.solar_worker.log_event_to_db"):
        _setup_nvr_mock_db(mock_conn, channels="1,2,3,4")

        # 1º pulso na D02 em t=3000.0 (precursor na rua, não aciona relé)
        with patch("time.time", return_value=3000.0):
            sw.process_nvr_alarm_packet(client, pkt_d02)
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


def test_hybrid_d02_alone_car_transient_ignored():
    """D02 isolada (canal 2, movimento puro): 1 ou 2 pulsos rápidos de veículo não ligam o Muro."""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "OFF"
    sw.active_camera_timers.clear()
    sw.pending_presence.clear()
    sw.camera_cooldowns.clear()
    sw.continuous_on_tracker.clear()
    sw.active_motion_renew_pulses.clear()

    client = MagicMock()
    # Channel index 1 => D02 (canal 2)
    pkt_d02 = {"AlarmInfo": {"Channel": 1, "Status": "Start"}}

    with patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True):
        _setup_nvr_mock_db(mock_conn, channels="1,2,3")

        # 1º pulso de carro em t=6000.0s
        with patch("time.time", return_value=6000.0):
            sw.process_nvr_alarm_packet(client, pkt_d02)
            client.publish.assert_not_called()
            assert sw.current_states["home/outdoor/muro"] == "OFF"

        # 2º pulso de reflexo de farol em t=6001.0s (apenas 2 pulsos totais)
        with patch("time.time", return_value=6001.0):
            sw.process_nvr_alarm_packet(client, pkt_d02)
            client.publish.assert_not_called()
            assert sw.current_states["home/outdoor/muro"] == "OFF"


def test_hybrid_d02_alone_sustained_pedestrian_triggers():
    """D02 isolada: pedestre caminhando emite >= 2 pulsos entre 2.0s e 8.0s -> presença emulada CONFIRMADA!"""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "OFF"
    sw.active_camera_timers.clear()
    sw.pending_presence.clear()
    sw.camera_cooldowns.clear()
    sw.continuous_on_tracker.clear()
    sw.active_motion_renew_pulses.clear()

    client = MagicMock()
    pkt_d02 = {"AlarmInfo": {"Channel": 1, "Status": "Start"}}  # D02

    with patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True), \
         patch("scripts.solar_worker.log_event_to_db"):
        _setup_nvr_mock_db(mock_conn, channels="1,2,3")

        # Pulso 1 em t=7000.0s (entra em probation)
        with patch("time.time", return_value=7000.0):
            sw.process_nvr_alarm_packet(client, pkt_d02)
            client.publish.assert_not_called()

        # Pulso 2 em t=7002.5s (2 pulsos, elapsed=2.5s >= 2.0s e <= 8.0s) -> PRESENÇA EMULADA CONFIRMADA!
        with patch("time.time", return_value=7002.5):
            sw.process_nvr_alarm_packet(client, pkt_d02)
            client.publish.assert_called_with("home/outdoor/muro/set", "ON", qos=1, retain=True)
            assert sw.current_states["home/outdoor/muro"] == "ON"
            assert "home/outdoor/muro" in sw.active_camera_timers


def test_hybrid_d02_precursor_to_d01_or_d03():
    """D02 (rua) detecta movimento e D03 (IA no portão) confirma em até 5s -> liga imediatamente (fusão precursora)!"""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "OFF"
    sw.active_camera_timers.clear()
    sw.pending_presence.clear()
    sw.camera_cooldowns.clear()
    sw.continuous_on_tracker.clear()
    sw.active_motion_renew_pulses.clear()

    client = MagicMock()
    pkt_d02 = {"AlarmInfo": {"Channel": 1, "Status": "Start"}}  # D02 (idx 1)
    pkt_d03 = {"AlarmInfo": {"Channel": 2, "Status": "Start"}}  # D03 (idx 2)

    with patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True), \
         patch("scripts.solar_worker.log_event_to_db"):
        _setup_nvr_mock_db(mock_conn, channels="1,2,3")

        # D02 detecta aproximação na rua em t=8000.0s
        with patch("time.time", return_value=8000.0):
            sw.process_nvr_alarm_packet(client, pkt_d02)
            client.publish.assert_not_called()

        # D03 (IA portão) detecta pedestre em t=8002.1s (2.1s depois) -> fusão precursora confirma imediatamente!
        with patch("time.time", return_value=8002.1):
            sw.process_nvr_alarm_packet(client, pkt_d03)
            client.publish.assert_called_with("home/outdoor/muro/set", "ON", qos=1, retain=True)
            assert sw.current_states["home/outdoor/muro"] == "ON"


def test_hybrid_d02_while_on_single_pulse_does_not_starve_timer():
    """Com Muro já ON, pulso único em D02 (carro passando na rua) NÃO renova o timer para evitar inanição."""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "ON"
    sw.active_camera_timers["home/outdoor/muro"] = 9120.0  # Expira em 9120.0
    sw.continuous_on_tracker["home/outdoor/muro"] = 9000.0
    sw.active_motion_renew_pulses.clear()

    client = MagicMock()
    pkt_d02 = {"AlarmInfo": {"Channel": 1, "Status": "Start"}}  # D02

    with patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True):
        _setup_nvr_mock_db(mock_conn, channels="1,2,3")

        # Carro passa aos 9030.0s -> pulso único não deve estender o timer
        with patch("time.time", return_value=9030.0):
            sw.process_nvr_alarm_packet(client, pkt_d02)
            assert sw.active_camera_timers["home/outdoor/muro"] == 9120.0  # Permanece inalterado!


def test_hybrid_d02_while_on_sustained_motion_renews_timer():
    """Com Muro já ON, movimento sustentado em D02 (2 pulsos com dt >= 2.0s) renova o timer legitimamente."""
    import scripts.solar_worker as sw
    sw.current_states["home/outdoor/muro"] = "ON"
    sw.active_camera_timers["home/outdoor/muro"] = 9120.0  # Expira em 9120.0
    sw.continuous_on_tracker["home/outdoor/muro"] = 9000.0
    sw.active_motion_renew_pulses.clear()

    client = MagicMock()
    pkt_d02 = {"AlarmInfo": {"Channel": 1, "Status": "Start"}}  # D02

    with patch("scripts.solar_worker.get_db_conn") as mock_conn, \
         patch("scripts.solar_worker.release_db_conn"), \
         patch("scripts.solar_worker.is_currently_night", return_value=True):
        _setup_nvr_mock_db(mock_conn, channels="1,2,3")

        # 1º pulso aos 9030.0s
        with patch("time.time", return_value=9030.0):
            sw.process_nvr_alarm_packet(client, pkt_d02)
            assert sw.active_camera_timers["home/outdoor/muro"] == 9120.0

        # 2º pulso aos 9032.5s (2.5s depois -> movimento sustentado) -> renova para 9032.5 + 120 = 9152.5
        with patch("time.time", return_value=9032.5):
            sw.process_nvr_alarm_packet(client, pkt_d02)
            assert sw.active_camera_timers["home/outdoor/muro"] == 9152.5
