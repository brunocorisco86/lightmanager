#!/usr/bin/env python3
"""
Cadastra o ponto 'Muro' na tabela light_points com auto_mode=False (acionamento por radar).
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

def get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "light_manager"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

def main():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, name, mqtt_topic, power_w, auto_mode FROM light_points WHERE mqtt_topic = 'home/outdoor/muro';")
        row = cur.fetchone()
        if row:
            print(f"ℹ️ Ponto 'Muro' já cadastrado: ID={row[0]}, Nome={row[1]}, Tópico={row[2]}, Power={row[3]}W, Auto={row[4]}")
        else:
            cur.execute("""
                INSERT INTO light_points (name, mqtt_topic, power_w, auto_mode)
                VALUES ('Muro', 'home/outdoor/muro', 20.0, FALSE)
                RETURNING id;
            """)
            point_id = cur.fetchone()[0]
            conn.commit()
            print(f"✅ Ponto 'Muro' cadastrado com sucesso! ID={point_id}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
