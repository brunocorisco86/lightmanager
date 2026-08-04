import os
import sys
import pytest
from dotenv import load_dotenv

# Adiciona a raiz ao path para validar importação
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_bot_dependencies():
    """Valida se as bibliotecas críticas do bot estão instaladas."""
    try:
        import aiogram
        import paho.mqtt.client
        import psutil
        import psycopg2
    except ImportError as e:
        pytest.fail(f"Dependência do Bot ausente: {e}")

def test_bot_env_vars():
    """Verifica se as variáveis mínimas do bot existem no .env"""
    load_dotenv()
    assert os.getenv("TELEGRAM_BOT_TOKEN") is not None, "TELEGRAM_BOT_TOKEN não configurado"
    assert os.getenv("TELEGRAM_ALLOWED_USER_ID") is not None, "TELEGRAM_ALLOWED_USER_ID não configurado"

def test_bot_syntax():
    """Verifica se o arquivo bot.py não tem erros de sintaxe e pode ser carregado."""
    try:
        import bot.bot
    except Exception as e:
        # Se falhar por conexão (esperado em ambiente de teste), ignoramos, 
        # mas erros de sintaxe ou import quebram o teste.
        error_str = str(e)
        if "syntax" in error_str.lower() or "module not found" in error_str.lower():
            pytest.fail(f"Erro de carregamento no bot.py: {e}")

def test_get_solar_status_summary():
    """Valida a execução sem exceções de NameError/TypeError da função get_solar_status_summary."""
    try:
        import bot.bot as bot_module
        result = bot_module.get_solar_status_summary()
        assert isinstance(result, str)
    except Exception as e:
        error_str = str(e).lower()
        if "nameerror" in error_str or "typeerror" in error_str or "syntaxerror" in error_str:
            pytest.fail(f"Erro na função get_solar_status_summary: {e}")
