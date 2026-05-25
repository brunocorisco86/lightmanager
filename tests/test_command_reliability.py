import os
import pytest
import time
from fastapi.testclient import TestClient
from web_api.main import app, mqtt_client

client = TestClient(app)

def test_command_mqtt_qos_delivery():
    """
    Valida se o comando é enviado com sucesso via API e se o MQTT está conectado.
    Testa a confiabilidade do endpoint de comando.
    """
    # Garante que o MQTT está "conectado" para o teste (ou mockado se necessário)
    # Aqui testamos a integração real se o broker estiver up
    
    payload = {
        "topic": "home/outdoor/frente",
        "action": "ON"
    }
    
    start_time = time.time()
    response = client.post("/api/command", json=payload)
    end_time = time.time()
    
    # Valida tempo de resposta (deve ser rápido mesmo com wait_for_publish)
    assert end_time - start_time < 1.5
    
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "sent"
        assert "home/outdoor/frente/set" in data["topic"]
    elif response.status_code == 503:
        pytest.skip("MQTT Broker offline, pulando teste de entrega real.")
    else:
        pytest.fail(f"Erro inesperado no comando: {response.status_code}")

def test_command_invalid_payload():
    """Valida rejeição de payloads malformados"""
    response = client.post("/api/command", json={"invalid": "data"})
    assert response.status_code == 422 # Unprocessable Entity (FastAPI default)

def test_rapid_commands():
    """Valida se a API aguenta múltiplos comandos rápidos sem travar o loop MQTT"""
    for i in range(5):
        action = "ON" if i % 2 == 0 else "OFF"
        response = client.post("/api/command", json={
            "topic": "home/outdoor/frente",
            "action": action
        })
        if response.status_code == 503: break
        assert response.status_code == 200
