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
        mock_cur.__enter__.return_value = mock_cur
        # Simulate psycopg2 context manager behavior: __exit__ calls close()
        mock_cur.__exit__.side_effect = lambda *args: mock_cur.close()
        return mock_conn, mock_cur

    @patch('solar_worker.psycopg2.connect')
    @patch('solar_worker.get_today_sun_data')
    def test_connection_and_cursor_management(self, mock_sun_data, mock_connect):
        mock_conn, mock_cur = self.setup_mocks(mock_connect)

        mock_sun_data.return_value = {
            "sunrise": "2023-10-27T06:00:00+00:00",
            "sunset": "2023-10-27T18:00:00+00:00"
        }

        mock_cur.fetchone.return_value = [1] # point_id
        mock_cur.fetchall.return_value = [
            ("home/outdoor/frente", 0, 0),
            ("home/outdoor/fundos", 0, 0)
        ]

        solar_worker.current_states = {
            "home/outdoor/frente": "OFF",
            "home/outdoor/fundos": "OFF",
        }

        with patch('solar_worker.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.hour = 10
            mock_now.strftime.return_value = "10:00"
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = MagicMock(side_effect=lambda x: MagicMock())

            client = MagicMock()
            solar_worker.run_automation_cycle(client)

        self.assertEqual(mock_connect.call_count, 1)
        self.assertEqual(mock_conn.cursor.call_count, 2)
        self.assertEqual(mock_cur.close.call_count, 2)
        self.assertEqual(mock_conn.commit.call_count, 2)

    @patch('solar_worker.psycopg2.connect')
    def test_on_message_cursor_management(self, mock_connect):
        mock_conn, mock_cur = self.setup_mocks(mock_connect)
        mock_cur.fetchone.return_value = [1]

        solar_worker.current_states = {}
        client = MagicMock()
        msg = MagicMock()
        msg.topic = "home/outdoor/frente/state"
        msg.payload.decode.return_value = "ON"

        solar_worker.on_message(client, None, msg)

        self.assertEqual(mock_connect.call_count, 1)
        self.assertEqual(mock_conn.cursor.call_count, 2)
        self.assertEqual(mock_cur.close.call_count, 2)
        self.assertEqual(mock_conn.commit.call_count, 1)

    @patch('solar_worker.psycopg2.connect')
    @patch('solar_worker.get_today_sun_data')
    def test_error_handling_rollback(self, mock_sun_data, mock_connect):
        mock_conn, mock_cur = self.setup_mocks(mock_connect)
        mock_sun_data.return_value = {
            "sunrise": "2023-10-27T06:00:00+00:00",
            "sunset": "2023-10-27T18:00:00+00:00"
        }

        # Trigger an error during execution of light_points fetch
        mock_cur.execute.side_effect = [None, Exception("DB Error")]

        solar_worker.current_states = {} # Empty to skip hourly log and go straight to points fetch
        with patch('solar_worker.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.hour = 10
            mock_now.strftime.return_value = "10:00"
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = MagicMock(side_effect=lambda x: MagicMock())

            client = MagicMock()
            solar_worker.run_automation_cycle(client)

        self.assertGreaterEqual(mock_conn.rollback.call_count, 1)
        self.assertEqual(mock_cur.close.call_count, 2)

if __name__ == '__main__':
    unittest.main()
