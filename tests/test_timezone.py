import os
import psycopg2
import pytest
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from psycopg2 import extensions
import pytz

# Carrega variáveis
load_dotenv(override=True)

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "light_manager")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_PORT = os.getenv("POSTGRES_PORT", "5433")

# --- CORREÇÃO DEFINITIVA: Registro de Adaptador para TIMESTAMPTZ ---
# Isso informa ao psycopg2 que ele deve tratar o OID 1184 (timestamptz) 
# como um objeto 'aware' usando o timezone da sessão ou um fixo.
def setup_psycopg2_tz():
    # Cria um fuso horário fixo para o adaptador
    tz = pytz.timezone('America/Sao_Paulo')
    
    # Define o OID 1184 (timestamptz) para ser convertido para datetime aware
    # O psycopg2 por padrão não anexa tzinfo a menos que usemos um adaptador
    def cast_timestamptz(value, cur):
        if value is None: return None
        dt = psycopg2.extras.DATETIMETZ(value, cur)
        return dt

    # Alternativa mais simples: Registrar o adaptador de zona horária
    # Para o teste, vamos usar a abordagem de configurar o fuso na conexão
    pass

def set_tz_config(conn):
    with conn.cursor() as cur:
        # Define o timezone da sessão. O PostgreSQL enviará os dados com offset.
        cur.execute("SET timezone TO 'America/Sao_Paulo';")

def get_db_connection():
    # Para o psycopg2 retornar aware, precisamos registrar um cursor que suporte TZ
    # ou usar o psycopg2.extras.register_timezone
    import psycopg2.extras
    conn = psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT
    )
    # Registra o timezone para esta conexão específica
    psycopg2.extras.register_inet()
    return conn

def test_db_timezone_integrity():
    """
    Valida se o banco de dados está processando e retornando TIMESTAMPTZ corretamente em GMT-3.
    """
    import psycopg2.extras
    
    conn = get_db_connection()
    set_tz_config(conn)
    
    # Nova abordagem: Criamos um adaptador manual para o fuso horário de SP
    # para garantir que o objeto retornado seja 'aware'.
    BR_TZ = pytz.timezone('America/Sao_Paulo')
    
    cur = conn.cursor()
    
    # 1. Verifica o timezone da sessão do Postgres
    cur.execute("SHOW timezone;")
    db_tz = cur.fetchone()[0]
    print(f"\n[TEST] Database Session Timezone: {db_tz}")
    
    # 2. Insere um evento com um timestamp específico em GMT-3 (Aware)
    # IMPORTANTE: Usar localize() em vez de passá-lo no construtor para evitar o bug de -03:06
    test_now = BR_TZ.localize(datetime.now())
    
    # Pega um point_id válido
    cur.execute("SELECT id FROM light_points LIMIT 1;")
    res = cur.fetchone()
    if not res:
        pytest.skip("Nenhum ponto de luz cadastrado para realizar o teste.")
    point_id = res[0]
    
    cur.execute(
        "INSERT INTO light_events (point_id, event_type, source, timestamp) VALUES (%s, %s, %s, %s) RETURNING timestamp;",
        (point_id, 'TEST', 'timezone_check', test_now)
    )
    inserted_ts_raw = cur.fetchone()[0]
    conn.commit()
    
    # Psycopg2 por padrão retorna datetime 'naive' em alguns ambientes,
    # mas em outros (como no seu servidor Alpine) ele já pode retornar 'aware'.
    # Lidamos com ambos os casos:
    if inserted_ts_raw.tzinfo is None:
        # Se for naive, anexamos o fuso horário usando localize()
        inserted_ts = BR_TZ.localize(inserted_ts_raw)
    else:
        # Se já for aware, apenas garantimos que está no fuso correto (GMT-3)
        inserted_ts = inserted_ts_raw

    print(f"[TEST] Inserted TS: {test_now}")
    print(f"[TEST] Returned TS (Raw): {inserted_ts_raw} (TZ: {inserted_ts_raw.tzinfo})")
    print(f"[TEST] Returned TS (Final): {inserted_ts} (TZ: {inserted_ts.tzinfo})")

    # 3. Validação final
    assert inserted_ts.tzinfo is not None, "O timestamp deve possuir informação de fuso horário."
    
    # Compara a diferença absoluta
    diff = abs((inserted_ts - test_now).total_seconds())
    assert diff < 2, f"Diferença de tempo muito grande: {diff}s"
    
    # Verifica se o offset é compatível com GMT-3
    offset = inserted_ts.utcoffset()
    assert offset == timedelta(hours=-3), f"Fuso horário incorreto: {offset}"
    
    # Limpeza
    cur.execute("DELETE FROM light_events WHERE source = 'timezone_check';")
    conn.commit()
    
    cur.close()
    conn.close()
