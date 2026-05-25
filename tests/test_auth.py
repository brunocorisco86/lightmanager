import os
import pytest
import bcrypt
import psycopg2
from fastapi.testclient import TestClient
from web_api.main import app

client = TestClient(app)

# Helper para conexão
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "light_manager"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", "5433")
    )

@pytest.fixture(autouse=True)
def setup_test_user():
    # Prepara um usuário de teste
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Limpa antes
    cur.execute("DELETE FROM users WHERE username = 'testuser'")
    
    # Cria senha hash
    password = "testpassword"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    cur.execute(
        "INSERT INTO users (username, hashed_password, full_name) VALUES (%s, %s, %s)",
        ('testuser', hashed, 'Test Bot')
    )
    conn.commit()
    cur.close()
    conn.close()
    
    yield
    
    # Limpa depois
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username = 'testuser'")
    conn.commit()
    cur.close()
    conn.close()

def test_login_success():
    """Valida login com credenciais corretas"""
    payload = {
        "username": "testuser",
        "password": "testpassword"
    }
    response = client.post("/api/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["username"] == "testuser"

def test_login_wrong_password():
    """Valida falha com senha incorreta"""
    payload = {
        "username": "testuser",
        "password": "wrongpassword"
    }
    response = client.post("/api/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

def test_login_user_not_found():
    """Valida falha com usuário inexistente"""
    payload = {
        "username": "nonexistent",
        "password": "somepassword"
    }
    response = client.post("/api/login", json=payload)
    assert response.status_code == 401
