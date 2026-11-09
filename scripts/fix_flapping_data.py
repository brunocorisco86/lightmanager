#!/usr/bin/env python3
"""
scripts/fix_flapping_data.py
Script de auditoria e consolidação de consumo elétrico gerado por flapping (B-03).
Identifica micro-fragmentos de acendimento gerados por oscilação indevida
e consolida em períodos limpos e contínuos de consumo.

Padrão de execução: --dry-run (somente leitura / simulação).
Para aplicar: --apply
"""

import os
import sys
import argparse
import psycopg2
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

BR_TZ = timezone(timedelta(hours=-3))

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "light_manager"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

def audit_and_fix(apply_changes=False, target_dates=None):
    if target_dates is None:
        target_dates = ["2026-11-07", "2026-11-08"]

    conn = get_db_connection()
    cur = conn.cursor()

    print(f"\n🔍 [B-03] Auditoria de Dados de Consumo (Flapping Incident)")
    print(f"Modo: {'⚠️ APLICAÇÃO REAL (--apply)' if apply_changes else '🛡️ SIMULAÇÃO (--dry-run)'}")
    print(f"Datas analisadas: {', '.join(target_dates)}\n" + "="*60)

    # Cria tabela de backup de segurança se for aplicar
    if apply_changes:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS light_consumption_backup_flapping (
                backup_id SERIAL PRIMARY KEY,
                backup_created_at TIMESTAMPTZ DEFAULT NOW(),
                id INT,
                point_id INT,
                on_timestamp TIMESTAMPTZ,
                off_timestamp TIMESTAMPTZ,
                duration_seconds INT,
                consumption_kwh NUMERIC(10, 4)
            );
        """)
        conn.commit()

    total_consolidated_records = 0

    for date_str in target_dates:
        print(f"\n📅 Data: {date_str} (Madrugada 02:00 às 06:30 BRT)")
        
        # Janela de análise da madrugada
        window_start = f"{date_str} 02:00:00-03"
        window_end = f"{date_str} 06:30:00-03"

        for point_id in [1, 2]:
            cur.execute("SELECT name, mqtt_topic, power_w FROM light_points WHERE id = %s", (point_id,))
            pt = cur.fetchone()
            if not pt:
                continue
            name, topic, power_w = pt[0], pt[1], float(pt[2])

            # Busca registros de duração curta (< 180s)
            cur.execute("""
                SELECT id, on_timestamp, off_timestamp, duration_seconds, consumption_kwh
                FROM light_consumption
                WHERE point_id = %s
                  AND on_timestamp >= %s
                  AND off_timestamp <= %s
                  AND duration_seconds <= 180
                ORDER BY on_timestamp ASC
            """, (point_id, window_start, window_end))

            rows = cur.fetchall()
            if not rows:
                print(f"  • Ponto {name} ({topic}): Nenhum micro-fragmento encontrado.")
                continue

            count = len(rows)
            total_sec_frag = sum(r[3] for r in rows)
            total_kwh_frag = sum(float(r[4]) for r in rows)
            first_on = rows[0][1]
            last_off = rows[-1][2]
            ids_to_replace = [r[0] for r in rows]

            # Duração consolidada entre o primeiro acendimento e o último desligamento da janela
            consolidated_duration_sec = int((last_off - first_on).total_seconds())
            consolidated_kwh = (consolidated_duration_sec / 3600.0) * (power_w / 1000.0)

            print(f"  • Ponto {name} (ID: {point_id}, {topic}):")
            print(f"    - Fragmentos detectados: {count} registros")
            print(f"    - Primeiro acendimento: {first_on.strftime('%H:%M:%S')} | Último: {last_off.strftime('%H:%M:%S')}")
            print(f"    - Soma atual dos fragmentos: {total_sec_frag}s (~{total_sec_frag/60:.1f} min), {total_kwh_frag:.4f} kWh")
            print(f"    - Consolidado contínuo:      {consolidated_duration_sec}s (~{consolidated_duration_sec/60:.1f} min), {consolidated_kwh:.4f} kWh")

            if apply_changes:
                # 1. Faz backup dos registros a serem substituídos
                cur.execute("""
                    INSERT INTO light_consumption_backup_flapping (id, point_id, on_timestamp, off_timestamp, duration_seconds, consumption_kwh)
                    SELECT id, point_id, on_timestamp, off_timestamp, duration_seconds, consumption_kwh
                    FROM light_consumption
                    WHERE id = ANY(%s)
                """, (ids_to_replace,))

                # 2. Remove os micro-fragmentos
                cur.execute("DELETE FROM light_consumption WHERE id = ANY(%s)", (ids_to_replace,))

                # 3. Insere o registro único consolidado
                cur.execute("""
                    INSERT INTO light_consumption (point_id, on_timestamp, off_timestamp, duration_seconds, consumption_kwh)
                    VALUES (%s, %s, %s, %s, %s)
                """, (point_id, first_on, last_off, consolidated_duration_sec, consolidated_kwh))

                conn.commit()
                print(f"    ✅ Sucesso: {count} micro-registros substituídos por 1 período consolidado contínuo!")
                total_consolidated_records += count

    print("\n" + "="*60)
    if apply_changes:
        print(f"🎉 Consolidação concluída! Total de {total_consolidated_records} fragmentos mesclados com backup preservado.")
    else:
        print(f"ℹ️ Execução em modo de simulação (--dry-run). Nenhuma alteração foi realizada no banco.")
        print(f"   Para consolidar definitivamente, execute com a flag: --apply")
    print("="*60 + "\n")

    cur.close()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auditoria e Consolidação de Consumo por Flapping (B-03)")
    parser.add_argument("--apply", action="store_true", help="Aplica as correções de consolidação no banco de dados")
    parser.add_argument("--dates", nargs="+", default=["2026-11-07", "2026-11-08"], help="Datas para auditar (formato YYYY-MM-DD)")
    args = parser.parse_args()

    audit_and_fix(apply_changes=args.apply, target_dates=args.dates)
