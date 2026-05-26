import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao path para localizar o pacote scripts
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.solar_worker import send_telegram_message

@patch("scripts.solar_worker.requests.post")
@patch("scripts.solar_worker.TG_TOKEN", "fake_token")
@patch("scripts.solar_worker.TG_USER_ID", "123456")
def test_send_telegram_message_success(mock_post):
    """Valida se a função de envio chama a URL correta do Telegram com o payload esperado."""
    # Configura o mock da resposta
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    send_telegram_message("Test message")

    # Verifica se o post foi chamado corretamente
    expected_url = "https://api.telegram.org/botfake_token/sendMessage"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == expected_url
    assert kwargs["json"]["chat_id"] == "123456"
    assert "Test message" in kwargs["json"]["text"]

@patch("scripts.solar_worker.requests.post")
@patch("scripts.solar_worker.TG_TOKEN", "fake_token")
@patch("scripts.solar_worker.TG_USER_ID", "123456")
def test_send_telegram_message_failure(mock_post):
    """Valida se a função trata erros de rede ou status sem quebrar o worker."""
    mock_post.side_effect = Exception("Network error")
    
    # Não deve subir exceção
    try:
        send_telegram_message("Should fail silently")
    except Exception as e:
        pytest.fail(f"send_telegram_message subiu exceção: {e}")

@patch("scripts.solar_worker.requests.post")
@patch("scripts.solar_worker.TG_TOKEN", None)
def test_send_telegram_message_no_config(mock_post):
    """Garante que nada é enviado se o token não estiver configurado."""
    send_telegram_message("No config")
    mock_post.assert_not_called()
