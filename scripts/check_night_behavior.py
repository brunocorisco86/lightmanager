#!/usr/bin/env python3
"""
scripts/check_night_behavior.py
Ferramenta de monitoramento e auditoria pós-madrugada para validar
se houve oscilação/flapping nas luzes antes da gravação de firmware (B-04).
"""

import os
import sys
import argparse
import psycopg2
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
BR_TZ = timezone(timedelta(hours=-3))

def analyze_night(target_date_str=None):
    if not target_date_str:
        now_br = datetime.now(BR_TZ)
        target_date_str = str(now_br.date())

    print(f"\n🌙 [Monitoramento Noturno] Auditoria de Estabilidade da Iluminação")
    print(f"Data Alvo: {target_date_str} (Janela Noturna: 00:00 às 07:00 BRT)\n" + "="*65)

    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "light_manager"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )
    cur = conn.cursor()

    window_start = f"{target_date_str} 00:00:00-03"
    window_end = f"{target_date_str} 07:00:00-03"

    for point_id in [2, 1]:  # Frente, Fundos
        cur.execute("SELECT name, mqtt_topic FROM light_points WHERE id = %s", (point_id,))
        pt = cur.fetchone()
        if not pt:
            continue
        name, topic = pt[0], pt[1]

        # 1. Contagem de eventos de estado
        cur.execute("""
            SELECT event_type, source, count(*)
            FROM light_events
            WHERE point_id = %s
              AND timestamp >= %s AND timestamp <= %s
            GROUP BY event_type, source
            ORDER BY count(*) DESC;
        """, (point_id, window_start, window_end))
        events_summary = cur.fetchall()

        # 2. Total de transições OFF
        cur.execute("""
            SELECT count(*)
            FROM light_events
            WHERE point_id = %s AND event_type = 'OFF'
              AND timestamp >= %s AND timestamp <= %s;
        """, (point_id, window_start, window_end))
        total_offs = cur.fetchone()[0]

        # 3. Micro-fragmentos de consumo
        cur.execute("""
            SELECT count(*), coalesce(sum(duration_seconds), 0)
            FROM light_consumption
            WHERE point_id = %s
              AND on_timestamp >= %s AND off_timestamp <= %s
              AND duration_seconds <= 180;
        """, (point_id, window_start, window_end))
        micro_res = cur.fetchone()
        micro_count, micro_secs = micro_res[0], micro_res[1]

        print(f"\n💡 Ponto: {name} (`{topic}`)")
        print(f"  • Desligamentos (OFF) registrados: {total_offs}")
        print(f"  • Micro-fragmentos (<180s):        {micro_count} ({micro_secs}s acumulados)")
        if events_summary:
            print("  • Distribuição por fonte:")
            for ev, src, cnt in events_summary:
                print(f"      - {src} [{ev}]: {cnt}x")

        # Classificação de Saúde
        if total_offs <= 2 and micro_count == 0:
            print(f"  • Diagnóstico: 🟢 ESTÁVEL (Sem flapping detectado)")
        elif total_offs > 10:
            print(f"  • Diagnóstico: 🚨 FLAPPING ATIVO ({total_offs} desvios na madrugada!)")
        else:
            print(f"  • Diagnóstico: ⚠️ ATENÇÃO (Pequenas oscilações observadas: {total_offs} OFFs)")

    cur.close()
    conn.close()

    # 4. Leitura do log de desvios do solar_worker
    log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'solar.log')
    if os.path.exists(log_path):
        desvios_count = 0
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if target_date_str in line and "Desvio detectado" in line:
                        desvios_count += 1
            print(f"\n📋 Ocorrências de 'Desvio detectado' no solar.log para {target_date_str}: {desvios_count}")
        except Exception as e:
            print(f"Aviso ao ler log: {e}")

    print("\n" + "="*65 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verifica o comportamento noturno das luzes")
    parser.add_argument("--date", help="Data a auditar (YYYY-MM-DD). Padrão: hoje")
    args = parser.parse_args()
    analyze_night(args.date)
