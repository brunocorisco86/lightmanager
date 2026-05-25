import os
import psycopg2
import pytest
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Carrega variáveis
load_dotenv(override=True)

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "light_manager")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_PORT = os.getenv("POSTGRES_PORT", "5433")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT
    )

def test_db_timezone_integrity():
    """
    Valida se o banco de dados está processando e retornando TIMESTAMPTZ corretamente em GMT-3.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Força o timezone da sessão para garantir o comportamento esperado
    cur.execute("SET timezone TO 'America/Sao_Paulo';")
    
    # 1. Verifica o timezone da sessão do Postgres
    cur.execute("SHOW timezone;")
    db_tz = cur.fetchone()[0]
    print(f"\n[TEST] Database Session Timezone: {db_tz}")
    
    # 2. Insere um evento com um timestamp específico em GMT-3 (Aware)
    BR_TZ = timezone(timedelta(hours=-3))
    test_now = datetime.now(BR_TZ)
    
    # Pega um point_id válido
    cur.execute("SELECT id FROM light_points LIMIT 1;")
    point_id = cur.fetchone()[0]
    
    cur.execute(
        "INSERT INTO light_events (point_id, event_type, source, timestamp) VALUES (%s, %s, %s, %s) RETURNING timestamp;",
        (point_id, 'TEST', 'timezone_check', test_now)
    )
    inserted_ts = cur.fetchone()[0]
    conn.commit()
    
    print(f"[TEST] Inserted TS: {test_now}")
    print(f"[TEST] Returned TS: {inserted_ts} (TZ: {inserted_ts.tzinfo})")

    # 3. Verifica se o offset está correto. 
    # Se o Postgres retorna naive em UTC (offset None), o assert falhará, 
    # o que indica que precisamos de configuração no adaptador ou no banco.
    assert inserted_ts.tzinfo is not None, "O timestamp retornado deve ser 'aware' (possuir fuso horário)."
    assert inserted_ts.utcoffset() == timedelta(hours=-3)
    
    # Limpeza
    cur.execute("DELETE FROM light_events WHERE source = 'timezone_check';")
    conn.commit()
    
    cur.close()
    conn.close()
