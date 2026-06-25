import os
import psycopg2
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "light_manager"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("==> Criando tabelas no banco de dados...")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS light_points (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            mqtt_topic VARCHAR(255) UNIQUE NOT NULL,
            power_w NUMERIC NOT NULL,
            auto_mode BOOLEAN DEFAULT TRUE,
            offset_on_minutes INTEGER DEFAULT 0,
            offset_off_minutes INTEGER DEFAULT 0,
            manual_override VARCHAR(10) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # Migração para bancos existentes
    cur.execute("ALTER TABLE light_points ADD COLUMN IF NOT EXISTS manual_override VARCHAR(10) DEFAULT NULL;")

    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS light_events (
            id SERIAL PRIMARY KEY,
            point_id INTEGER REFERENCES light_points(id) ON DELETE CASCADE,
            event_type VARCHAR(10) NOT NULL,
            source VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS light_consumption (
            id SERIAL PRIMARY KEY,
            point_id INTEGER REFERENCES light_points(id) ON DELETE CASCADE,
            on_timestamp TIMESTAMPTZ NOT NULL,
            off_timestamp TIMESTAMPTZ NOT NULL,
            duration_seconds INTEGER NOT NULL,
            consumption_kwh NUMERIC(10, 4) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print("==> Tabelas criadas com sucesso.")

def register_point(name, topic, power):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO light_points (name, mqtt_topic, power_w) VALUES (%s, %s, %s) RETURNING id;",
            (name, topic, power)
        )
        point_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ Ponto '{name}' registrado com sucesso! (ID: {point_id})")
    except psycopg2.IntegrityError:
        conn.rollback()
        print(f"⚠️ O tópico MQTT '{topic}' já está cadastrado no banco.")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    # 1. Garante que o banco está pronto
    init_db()
    
    print("\n--- Cadastro de Pontos de Luz ---")
    print("Pressione Ctrl+C para sair.\n")
    
    # 2. Loop interativo para cadastro
    while True:
        try:
            name = input("Nome do local (ex: Frente, Fundos): ").strip()
            if not name: continue
            
            topic = input(f"Tópico MQTT (ex: home/outdoor/{name.lower()}): ").strip()
            if not topic: continue
            
            power_str = input("Potência da lâmpada em Watts (ex: 60): ").strip()
            power = float(power_str)
            
            register_point(name, topic, power)
            print("-" * 30)
        except ValueError:
            print("❌ Erro: Potência deve ser um número.")
        except KeyboardInterrupt:
            print("\nSaindo...")
            break
