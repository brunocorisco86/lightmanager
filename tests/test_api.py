import requests
import pytest
import os
from dotenv import load_dotenv

# Carrega variáveis para o teste
load_dotenv()

LAT = os.getenv("LATITUDE", "-23.5505")
LONG = os.getenv("LONGITUDE", "-46.6333")

def test_sunrise_sunset_api_iso_format():
    """
    Testa se a API responde corretamente com formatted=0 (ISO 8601).
    Isso valida a premissa usada no solar_worker.py e no web_api.
    """
    url = f"https://api.sunrise-sunset.org/json?lat={LAT}&lng={LONG}&formatted=0"
    
    response = requests.get(url, timeout=10)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "OK"
    
    results = data["results"]
    assert "sunrise" in results
    assert "sunset" in results
    
    # Verifica se o formato é ISO (contém 'T' e '+')
    assert "T" in results["sunrise"]
    assert "+" in results["sunrise"] or "Z" in results["sunrise"].upper()
    
    print(f"\n[TEST] Sunrise (UTC): {results['sunrise']}")
    print(f"[TEST] Sunset (UTC): {results['sunset']}")

def test_sunrise_sunset_api_parameters():
    """
    Valida os parâmetros do request_parameters.md.
    """
    # Testando com data específica e tzid
    url = f"https://api.sunrise-sunset.org/json?lat={LAT}&lng={LONG}&formatted=0&date=2026-05-22&tzid=America/Sao_Paulo"
    
    response = requests.get(url, timeout=10)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "OK"
    assert data["tzid"] == "America/Sao_Paulo"
    
    results = data["results"]
    # Com tzid, o horário deve vir ajustado (ex: -03:00)
    assert "-03:00" in results["sunrise"] or "-02:00" in results["sunrise"] # Depende de horário de verão se houver
