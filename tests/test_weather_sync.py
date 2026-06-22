import os
import sys
from unittest.mock import MagicMock, patch
import pytest
import numpy as np
import pytz
from datetime import datetime

# Adiciona o diretório scripts ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import weather_offset_sync

@patch("weather_offset_sync.openmeteo_requests.Client")
@patch("weather_offset_sync.get_db_connection")
@patch("weather_offset_sync.requests_cache.CachedSession")
@pytest.mark.parametrize(
    "cloud_cover_val,expected_on,expected_off",
    [
        (100.0, -10, 10),
        (0.0, 10, -10),
        (50.0, 0, 0),
        (25.0, 5, -5),
        (75.0, -5, 5),
    ]
)
def test_weather_offset_sync(mock_cache, mock_db_conn, mock_openmeteo_client, cloud_cover_val, expected_on, expected_off):
    # Configura mocks de banco de dados
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_db_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    
    # Configura mocks do cliente OpenMeteo
    mock_client = MagicMock()
    mock_openmeteo_client.return_value = mock_client
    
    mock_response = MagicMock()
    mock_client.weather_api.return_value = [mock_response]
    
    # Configura dados horários de previsão
    mock_hourly = MagicMock()
    mock_response.Hourly.return_value = mock_hourly
    
    # Usamos timestamp de agora
    tz = pytz.timezone("America/Sao_Paulo")
    now = datetime.now(tz)
    base_timestamp = int(now.timestamp()) - 1800 # 30 min atrás para garantir que 'now' caia na primeira hora
    
    mock_hourly.Time.return_value = base_timestamp
    mock_hourly.TimeEnd.return_value = base_timestamp + 7200
    mock_hourly.Interval.return_value = 3600
    mock_response.Timezone.return_value = b"America/Sao_Paulo"
    
    mock_variable = MagicMock()
    mock_variable.ValuesAsNumpy.return_value = np.array([cloud_cover_val, cloud_cover_val], dtype=np.float32)
    mock_hourly.Variables.return_value = mock_variable
    
    # Executa a função principal do sincronizador
    weather_offset_sync.main()
    
    # Verifica se a query de atualização do banco foi chamada com os valores esperados
    mock_cur.execute.assert_called_with(
        "UPDATE light_points SET offset_on_minutes = %s, offset_off_minutes = %s;",
        (expected_on, expected_off)
    )
    mock_conn.commit.assert_called_once()
    mock_cur.close.assert_called_once()
    mock_conn.close.assert_called_once()
