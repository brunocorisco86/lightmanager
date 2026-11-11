import unittest
from unittest.mock import MagicMock, patch, call
import sys
import os

# Mocking all dependencies that might be missing
sys.modules['paho'] = MagicMock()
sys.modules['paho.mqtt'] = MagicMock()
sys.modules['paho.mqtt.client'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Add the scripts directory to path so we can import solar_worker
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

import solar_worker

class TestSolarWorkerPerformance(unittest.TestCase):
    def setUp(self):
        # Reset global state
        solar_worker.db_conn = None
        solar_worker.last_hour_logged = -1

    def setup_mocks(self, mock_connect):
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.connection = mock_conn
        mock_cur.__enter__.return_value = mock_cur
        # Simulate psycopg2 context manager behavior: __exit__ calls close()
        mock_cur.__exit__.side_effect = lambda *args: mock_cur.close()
        return mock_conn, mock_cur

    @patch('solar_worker.get_db_conn')
    @patch('solar_worker.get_today_sun_data')
    def test_connection_and_cursor_management(self, mock_sun_data, mock_get_db_conn):
        mock_conn, mock_cur = self.setup_mocks(mock_get_db_conn)

        mock_sun_data.return_value = {
            "sunrise": "2023-10-27T06:00:00+00:00",
            "sunset": "2023-10-27T18:00:00+00:00"
        }

        mock_cur.fetchone.return_value = [1] # point_id
        mock_cur.fetchall.side_effect = [
            [(0, 0), (0, 0)],  # For the fallback calculation query (offset_on, offset_off)
            [(1, "home/outdoor/frente", 0, 0, None), (2, "home/outdoor/fundos", 0, 0, None)]  # For the point list query (id, topic, on, off, manual_override)
        ]

        solar_worker.current_states = {
            "home/outdoor/frente": "OFF",
            "home/outdoor/fundos": "OFF",
        }

        from datetime import datetime as dt_real
        with patch('solar_worker.datetime') as mock_datetime:
            mock_now = dt_real(2023, 10, 27, 10, 0, 0, tzinfo=solar_worker.BR_TZ)
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = MagicMock(side_effect=lambda x: dt_real.fromisoformat(x))

            client = MagicMock()
            solar_worker.run_automation_cycle(client)

        self.assertEqual(mock_get_db_conn.call_count, 1)
        self.assertEqual(mock_conn.cursor.call_count, 1)
        self.assertEqual(mock_cur.close.call_count, 1)
        self.assertEqual(mock_conn.commit.call_count, 2)

    @patch('solar_worker.get_db_conn')
    def test_on_message_cursor_management(self, mock_get_db_conn):
        mock_conn, mock_cur = self.setup_mocks(mock_get_db_conn)
        mock_cur.fetchone.return_value = [1]

        solar_worker.current_states = {}
        client = MagicMock()
        msg = MagicMock()
        msg.topic = "home/outdoor/frente/state"
        msg.payload.decode.return_value = "ON"

        solar_worker.on_message(client, None, msg)

        self.assertEqual(mock_get_db_conn.call_count, 1)
        self.assertEqual(mock_conn.cursor.call_count, 1)
        self.assertEqual(mock_cur.close.call_count, 1)
        self.assertEqual(mock_conn.commit.call_count, 1)

    @patch('solar_worker.get_db_conn')
    def test_on_message_consumption_calculation(self, mock_get_db_conn):
        mock_conn, mock_cur = self.setup_mocks(mock_get_db_conn)
        
        # Simulate timezone-aware current time: 2026-06-23 12:00:00 (America/Sao_Paulo)
        from datetime import datetime as dt_real
        now_br = dt_real(2026, 6, 23, 12, 0, 0, tzinfo=solar_worker.BR_TZ)
        on_ts = dt_real(2026, 6, 23, 10, 0, 0, tzinfo=solar_worker.BR_TZ) # 2 hours prior
        
        fetchone_values = [
            [1],       # query 1: point_id
            [on_ts],   # query 2: ON event timestamp
            None,      # query 3: OFF event timestamp (None)
            [100.0]    # query 4: power_w (100W)
        ]
        mock_cur.fetchone.side_effect = fetchone_values

        solar_worker.current_states = {"home/outdoor/frente": "ON"}
        
        with patch('solar_worker.datetime') as mock_datetime:
            mock_datetime.now.return_value = now_br
            
            client = MagicMock()
            msg = MagicMock()
            msg.topic = "home/outdoor/frente/state"
            msg.payload.decode.return_value = "OFF"
            
            solar_worker.on_message(client, None, msg)

        # Check that we queried the db queries
        # The 4 queries should have been run in sequence.
        self.assertEqual(mock_cur.execute.call_count, 6) # 4 queries + 2 inserts (light_consumption and light_events)
        
        calls = mock_cur.execute.call_args_list
        insert_consumption_call = None
        for c in calls:
            query_str = c[0][0]
            if "INSERT INTO light_consumption" in query_str:
                insert_consumption_call = c
                break
        
        self.assertIsNotNone(insert_consumption_call, "INSERT INTO light_consumption query was not executed.")
        args = insert_consumption_call[0][1]
        self.assertEqual(args[0], 1) # point_id
        self.assertEqual(args[1], on_ts) # on_timestamp
        self.assertEqual(args[2], now_br) # off_timestamp
        self.assertEqual(args[3], 7200) # duration_seconds (2 hours = 7200s)
        self.assertEqual(args[4], 0.2) # consumption_kwh: (7200 / 3600) * (100 / 1000) = 2 * 0.1 = 0.2 kWh

    @patch('solar_worker.get_db_conn')
    @patch('solar_worker.get_today_sun_data')
    def test_error_handling_rollback(self, mock_sun_data, mock_get_db_conn):
        mock_conn, mock_cur = self.setup_mocks(mock_get_db_conn)
        mock_sun_data.return_value = {
            "sunrise": "2023-10-27T06:00:00+00:00",
            "sunset": "2023-10-27T18:00:00+00:00"
        }

        # Trigger an error during execution of light_points fetch
        mock_cur.execute.side_effect = Exception("DB Error")

        solar_worker.current_states = {} # Empty to skip hourly log and go straight to points fetch
        from datetime import datetime as dt_real
        with patch('solar_worker.datetime') as mock_datetime:
            mock_now = dt_real(2023, 10, 27, 10, 0, 0, tzinfo=solar_worker.BR_TZ)
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = MagicMock(side_effect=lambda x: dt_real.fromisoformat(x))

            client = MagicMock()
            solar_worker.run_automation_cycle(client)

        self.assertGreaterEqual(mock_conn.rollback.call_count, 1)
        self.assertEqual(mock_cur.close.call_count, 1)

    @patch('solar_worker.get_db_conn')
    def test_on_message_heartbeat_sync(self, mock_get_db_conn):
        mock_conn, mock_cur = self.setup_mocks(mock_get_db_conn)
        mock_cur.fetchone.return_value = [1] # point_id

        # Estado inicial limpo
        solar_worker.current_states = {"home/outdoor/frente": "OFF", "home/outdoor/fundos": "OFF"}
        client = MagicMock()
        msg = MagicMock()
        msg.topic = "home/outdoor/status"
        # Heartbeat informando que frente está ON e fundos está OFF (fundos não mudou)
        msg.payload.decode.return_value = '{"status":"online","frente":"ON","fundos":"OFF","rssi":-50,"ip":"192.168.1.111"}'

        solar_worker.on_message(client, None, msg)

        # Deve ter atualizado current_states
        self.assertEqual(solar_worker.current_states.get("home/outdoor/frente"), "ON")
        self.assertEqual(solar_worker.current_states.get("home/outdoor/fundos"), "OFF")

        # Deve ter registrado o evento no banco de dados com source="heartbeat_sync"
        calls = mock_cur.execute.call_args_list
        insert_event_call = None
        for c in calls:
            query_str = c[0][0]
            if "INSERT INTO light_events" in query_str:
                insert_event_call = c
                break

        self.assertIsNotNone(insert_event_call)
        args = insert_event_call[0][1]
        self.assertEqual(args[1], "ON") # event_type
        self.assertEqual(args[2], "heartbeat_sync") # source

    @patch('solar_worker.get_db_conn')
    @patch('solar_worker.get_today_sun_data')
    @patch('solar_worker.time')
    def test_run_automation_cycle_time_publication(self, mock_time, mock_sun_data, mock_get_db_conn):
        mock_conn, mock_cur = self.setup_mocks(mock_get_db_conn)
        mock_sun_data.return_value = {
            "sunrise": "2023-10-27T06:00:00+00:00",
            "sunset": "2023-10-27T18:00:00+00:00"
        }
        mock_cur.fetchall.return_value = [] # sem pontos para simplificar o loop

        # Mock o timestamp da hora atual como 1782288000
        mock_time.time.return_value = 1782288000

        client = MagicMock()
        solar_worker.run_automation_cycle(client)

        # Verifica se publicou a hora atual no tópico home/outdoor/time
        client.publish.assert_any_call("home/outdoor/time", "1782288000", qos=1, retain=False)

    @patch('solar_worker.get_db_conn')
    def test_run_day_rollover(self, mock_get_db_conn):
        mock_conn, mock_cur = self.setup_mocks(mock_get_db_conn)
        
        from datetime import datetime as dt_real
        now_br = dt_real(2026, 6, 23, 23, 59, 15, tzinfo=solar_worker.BR_TZ)
        on_ts = dt_real(2026, 6, 23, 20, 0, 0, tzinfo=solar_worker.BR_TZ)
        
        fetchone_values = [
            (1, 100.0), # point_id (1) and power_w (100W)
            (on_ts,)    # ON event timestamp
        ]
        mock_cur.fetchone.side_effect = fetchone_values

        solar_worker.current_states = {"home/outdoor/frente": "ON"}
        
        with patch('solar_worker.datetime') as mock_datetime:
            mock_datetime.now.return_value = now_br
            solar_worker.run_day_rollover()

        calls = mock_cur.execute.call_args_list
        insert_consumption_call = None
        insert_events_calls = []
        for c in calls:
            query_str = c[0][0]
            if "INSERT INTO light_consumption" in query_str:
                insert_consumption_call = c
            elif "INSERT INTO light_events" in query_str:
                insert_events_calls.append(c)

        self.assertIsNotNone(insert_consumption_call)
        args_consumption = insert_consumption_call[0][1]
        self.assertEqual(args_consumption[0], 1)
        self.assertEqual(args_consumption[1], on_ts)
        self.assertEqual(args_consumption[2], dt_real(2026, 6, 23, 23, 59, 59, tzinfo=solar_worker.BR_TZ))
        self.assertEqual(args_consumption[3], 14399)
        self.assertAlmostEqual(args_consumption[4], 0.39997, places=4)
        
        self.assertEqual(len(insert_events_calls), 2)
        args_event_off = insert_events_calls[0][0][1]
        self.assertEqual(args_event_off[1], "OFF")
        self.assertEqual(args_event_off[2], "day_rollover")
        self.assertEqual(args_event_off[3], dt_real(2026, 6, 23, 23, 59, 59, tzinfo=solar_worker.BR_TZ))
        
        args_event_on = insert_events_calls[1][0][1]
        self.assertEqual(args_event_on[1], "ON")
        self.assertEqual(args_event_on[2], "day_rollover")
        self.assertEqual(args_event_on[3], dt_real(2026, 6, 24, 0, 0, 0, tzinfo=solar_worker.BR_TZ))

    @patch('solar_worker.get_db_conn')
    @patch('solar_worker.is_currently_night', return_value=True)
    @patch('solar_worker.time')
    def test_nvr_camera_trigger_and_timeout_off(self, mock_time, mock_is_night, mock_get_db_conn):
        mock_conn, mock_cur = self.setup_mocks(mock_get_db_conn)

        # Point configured for camera mode on D03, D04 with 120s hold timer
        mock_cur.fetchall.return_value = [
            (3, "Muro", "home/outdoor/muro", "3,4", 120, True)
        ]
        mock_cur.fetchone.return_value = [3]

        solar_worker.current_states = {"home/outdoor/muro": "OFF"}
        solar_worker.active_camera_timers.clear()
        solar_worker.pending_presence.clear()
        solar_worker.camera_cooldowns.clear()
        solar_worker.continuous_on_tracker.clear()
        solar_worker.last_nvr_detection_ts.clear()
        mock_time.time.return_value = 1000.0

        client = MagicMock()
        alarm_pkt = {
            "AlarmInfo": {
                "Channel": 2,  # 0-based index 2 => D03 (channel 3)
                "Event": "MotionDetect",
                "Status": "Start",
                "StartTime": "2026-11-05 21:00:00"
            },
            "Name": "AlarmInfo"
        }

        # 1st pulse at t=1000.0 from D03 (AI camera): Confirms human immediately and turns relay ON
        solar_worker.process_nvr_alarm_packet(client, alarm_pkt)
        client.publish.assert_called_with("home/outdoor/muro/set", "ON", qos=1, retain=True)
        self.assertEqual(solar_worker.current_states.get("home/outdoor/muro"), "ON")
        self.assertIn("home/outdoor/muro", solar_worker.active_camera_timers)
        self.assertEqual(solar_worker.active_camera_timers["home/outdoor/muro"], 1120.0)

        # 2nd pulse 3 seconds later (t=1003.0) from same walk-by:
        # Renews hold timer to 1123.0, but debounce prevents duplicate INSERT INTO nvr_detections
        mock_time.time.return_value = 1003.0
        solar_worker.process_nvr_alarm_packet(client, alarm_pkt)
        self.assertEqual(solar_worker.active_camera_timers["home/outdoor/muro"], 1123.0)

        nvr_det_inserts = [
            c for c in mock_cur.execute.call_args_list
            if "INSERT INTO nvr_detections" in c[0][0]
        ]
        self.assertEqual(len(nvr_det_inserts), 1)

        # Before timer expires (at t=1050.0), should remain ON
        client.publish.reset_mock()
        solar_worker.check_expired_camera_timers(client, now_ts=1050.0)
        client.publish.assert_not_called()
        self.assertEqual(solar_worker.current_states.get("home/outdoor/muro"), "ON")

        # At t=1123.0 (after 120s from last packet), must publish OFF to Broker MQTT
        solar_worker.check_expired_camera_timers(client, now_ts=1123.0)
        client.publish.assert_called_with("home/outdoor/muro/set", "OFF", qos=1, retain=True)
        self.assertEqual(solar_worker.current_states.get("home/outdoor/muro"), "OFF")
        self.assertNotIn("home/outdoor/muro", solar_worker.active_camera_timers)

if __name__ == '__main__':
    unittest.main()
