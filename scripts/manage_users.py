import os
import psycopg2
from passlib.context import CryptContext
from dotenv import load_dotenv

# Carrega variáveis
load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "light_manager"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", "5433")
    )

def init_users_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def create_user(username, password, full_name="Admin"):
    hashed = pwd_context.hash(password)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, hashed_password, full_name) VALUES (%s, %s, %s)",
            (username, hashed, full_name)
        )
        conn.commit()
        print(f"✅ Usuário '{username}' criado com sucesso!")
    except psycopg2.IntegrityError:
        print(f"⚠️ Usuário '{username}' já existe.")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    init_users_table()
    print("\n--- Gerenciador de Usuários Light Manager ---")
    u = input("Digite o nome de usuário: ").strip()
    p = input("Digite a senha: ").strip()
    if u and p:
        create_user(u, p)
