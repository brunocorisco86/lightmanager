import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone, timedelta

# Adiciona a pasta scripts ao path do sistema para permitir a importação
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import solar_worker

class TestAutomationImprovements(unittest.TestCase):
    def setUp(self):
        # Limpa estados globais do worker
        solar_worker.current_states = {}
        solar_worker.last_hour_logged = -1

    def setup_mocks(self, mock_get_db_conn):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.connection = mock_conn
        mock_cur.__enter__.return_value = mock_cur
        mock_cur.__exit__.side_effect = lambda *args: mock_cur.close()
        return mock_conn, mock_cur

    @patch("solar_worker.get_db_pool")
    @patch("solar_worker.get_db_conn")
    @patch("solar_worker.get_today_sun_data")
    def test_dynamic_fallback_calculation(self, mock_sun_data, mock_get_db_conn, mock_get_db_pool):
        """Valida se os horários de fallback enviados ao Wemos se ajustam aos offsets corretos."""
        mock_conn, mock_cur = self.setup_mocks(mock_get_db_conn)

        # Configura dados do sol de hoje (Pôr do sol: 18:00 BRT, Nascer do sol: 06:00 BRT)
        mock_sun_data.return_value = {
            "sunrise": "2023-10-27T09:00:00+00:00",
            "sunset": "2023-10-27T21:00:00+00:00"
        }

        # Mock de banco com duas lâmpadas automáticas que usam offsets distintos:
        # Ponto 1: Ligar=+10 min (18:10), Desligar=-10 min (05:50)
        # Ponto 2: Ligar=+5 min (18:05), Desligar=-15 min (05:45)
        # Esperado: 
        #   Fallback Ligar: min(5, 10) - 1 = 4 min -> 18:00 + 4 = 18:04
        #   Fallback Desligar: max(-10, -15) + 1 = -9 min -> 06:00 - 9 = 05:51
        mock_cur.fetchall.side_effect = [
            [(10, -10), (5, -15)],  # Query 1: Fallback (offset_on, offset_off)
            []                      # Query 2: Points loop (id, topic, on, off, manual_override)
        ]

        from datetime import datetime as dt_real
        with patch("solar_worker.datetime") as mock_datetime:
            # Força o horário a ser 10:00 da manhã (para disparar verificação horária)
            mock_now = dt_real(2023, 10, 27, 10, 0, 0, tzinfo=solar_worker.BR_TZ)
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = MagicMock(side_effect=lambda x: dt_real.fromisoformat(x))

            client = MagicMock()
            solar_worker.run_automation_cycle(client)

            # Verifica se os payloads MQTT publicados usam os horários calculados dinamicamente
            client.publish.assert_any_call("home/outdoor/fallback/on", "18:04", qos=1, retain=True)
            client.publish.assert_any_call("home/outdoor/fallback/off", "05:51", qos=1, retain=True)

    @patch("solar_worker.get_db_pool")
    @patch("solar_worker.get_db_conn")
    @patch("solar_worker.get_today_sun_data")
    def test_manual_override_respected(self, mock_sun_data, mock_get_db_conn, mock_get_db_pool):
        """Verifica se o manual_override ativa o estado desejado forçado independentemente da hora solar."""
        mock_conn, mock_cur = self.setup_mocks(mock_get_db_conn)

        mock_sun_data.return_value = {
            "sunrise": "2023-10-27T09:00:00+00:00",
            "sunset": "2023-10-27T21:00:00+00:00"
        }

        # Query 1: auto_points (não é verificação horária, pula)
        # Query 2: points loop com manual_override
        # Ponto 1: Ligar=+10 min. Mas manual_override = 'OFF' em período noturno.
        # Ponto 2: Ligar=+10 min. Mas manual_override = 'ON' em período diurno.
        mock_cur.fetchall.side_effect = [
            [(1, "home/outdoor/frente", 10, -10, "OFF"), (2, "home/outdoor/fundos", 10, -10, "ON")]
        ]

        # Define estados em memória
        solar_worker.current_states = {
            "home/outdoor/frente": "ON",  # Desvio detectado (Desejado=OFF, Atual=ON)
            "home/outdoor/fundos": "OFF"  # Desvio detectado (Desejado=ON, Atual=OFF)
        }

        # Define hora atual como 20:00 da noite (deveria ser ON por padrão)
        from datetime import datetime as dt_real
        with patch("solar_worker.datetime") as mock_datetime:
            mock_now = dt_real(2023, 10, 27, 20, 0, 0, tzinfo=solar_worker.BR_TZ)
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = MagicMock(side_effect=lambda x: dt_real.fromisoformat(x))

            # Evita disparar a verificação horária
            solar_worker.last_hour_logged = 20

            client = MagicMock()
            solar_worker.run_automation_cycle(client)

            # Verifica se o worker forçou os estados do override manual
            # Frente: Forçado para OFF
            client.publish.assert_any_call("home/outdoor/frente/set", "OFF", qos=1, retain=True)
            # Fundos: Forçado para ON
            client.publish.assert_any_call("home/outdoor/fundos/set", "ON", qos=1, retain=True)

    @patch("solar_worker.get_db_pool")
    @patch("solar_worker.get_db_conn")
    @patch("solar_worker.get_today_sun_data")
    def test_manual_override_cleared_on_trigger(self, mock_sun_data, mock_get_db_conn, mock_get_db_pool):
        """Valida se o manual_override é limpo no banco ao bater o minuto do gatilho solar."""
        mock_conn, mock_cur = self.setup_mocks(mock_get_db_conn)

        mock_sun_data.return_value = {
            "sunrise": "2023-10-27T09:00:00+00:00",
            "sunset": "2023-10-27T21:00:00+00:00"
        }

        # Query 1: points loop
        mock_cur.fetchall.side_effect = [
            [(1, "home/outdoor/frente", 10, -10, "OFF")]
        ]

        # Define hora atual exatamente como 18:10 (Minuto exato do gatilho de ligar: sunset 18:00 + 10 min)
        from datetime import datetime as dt_real
        with patch("solar_worker.datetime") as mock_datetime:
            mock_now = dt_real(2023, 10, 27, 18, 10, 0, tzinfo=solar_worker.BR_TZ)
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = MagicMock(side_effect=lambda x: dt_real.fromisoformat(x))

            solar_worker.last_hour_logged = 18

            client = MagicMock()
            solar_worker.run_automation_cycle(client)

            # O gatilho solar deve atualizar a coluna manual_override para NULL no banco de dados
            mock_cur.execute.assert_any_call(
                "UPDATE light_points SET manual_override = NULL WHERE id = %s",
                (1,)
            )
            mock_conn.commit.assert_called()

if __name__ == "__main__":
    unittest.main()
