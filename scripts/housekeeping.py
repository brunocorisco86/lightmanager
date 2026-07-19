#!/usr/bin/env python3
# scripts/housekeeping.py
# Script de manutenção (housekeeping) do Light Manager:
# 1. Pruna eventos antigos no banco PostgreSQL (light_events > 7 dias)
# 2. Rotaciona e remove logs antigos (> 7 dias)
# 3. Garante e verifica permissões e sanidade do Mosquitto broker (/var/lib/mosquitto/ e /var/log/mosquitto/)

import os
import sys
import glob
import subprocess
import argparse
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(BASE_DIR, '..')
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

# Timezone de Brasília (GMT-3)
SP_TZ = timezone(timedelta(hours=-3))

def get_db_connection():
    """Tenta conectar ao PostgreSQL usando variáveis de ambiente do .env."""
    try:
        import psycopg2
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return psycopg2.connect(db_url)
        return psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB") or os.getenv("DB_NAME", "light_manager"),
            user=os.getenv("POSTGRES_USER") or os.getenv("DB_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASS", "postgres"),
            host=os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT", "5432")
        )
    except Exception as e:
        print(f"⚠️ [HOUSEKEEPING] Não foi possível conectar ao PostgreSQL: {e}")
        return None

def prune_database(days=7, dry_run=False):
    """Pruna os eventos na tabela light_events mais antigos que N dias."""
    cutoff_date = datetime.now(SP_TZ) - timedelta(days=days)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S%z')
    print(f"🧹 [HOUSEKEEPING] Verificando eventos do banco mais antigos que {days} dias (Corte: {cutoff_str})...")

    conn = get_db_connection()
    if not conn:
        print("⚠️ [HOUSEKEEPING] Pulando limpeza do banco de dados (sem conexão).")
        return 0

    try:
        with conn.cursor() as cur:
            if dry_run:
                cur.execute("SELECT COUNT(*) FROM light_events WHERE timestamp < %s;", (cutoff_date,))
                count = cur.fetchone()[0]
                print(f"🔍 [DRY-RUN] Encontrados {count} registros em 'light_events' para deletar.")
                return count
            else:
                cur.execute("DELETE FROM light_events WHERE timestamp < %s;", (cutoff_date,))
                count = cur.rowcount
                conn.commit()
                print(f"✅ [HOUSEKEEPING] Deletados {count} registros antigos da tabela 'light_events'.")
                return count
    except Exception as e:
        print(f"❌ [HOUSEKEEPING] Erro ao deletar registros antigos do banco: {e}")
        if conn:
            conn.rollback()
        return 0
    finally:
        if conn:
            conn.close()

def prune_logs(days=7, dry_run=False):
    """Roda logrotate e deleta arquivos de log rotacionados/comprimidos mais antigos que N dias."""
    print(f"🧹 [HOUSEKEEPING] Executando rotação e limpeza de logs (> {days} dias)...")
    logs_dir = os.path.join(PROJECT_ROOT, 'logs')
    logrotate_conf = os.path.join(PROJECT_ROOT, 'scripts', 'logrotate.conf')
    status_file = os.path.join(logs_dir, 'logrotate.status')

    # Executa logrotate se o utilitário estiver disponível
    if os.path.exists(logrotate_conf):
        try:
            cmd = ["logrotate", "-s", status_file, logrotate_conf]
            if dry_run:
                print(f"🔍 [DRY-RUN] Comando logrotate: {' '.join(cmd)}")
            else:
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    print("✅ [HOUSEKEEPING] logrotate executado com sucesso.")
                else:
                    print(f"⚠️ [HOUSEKEEPING] Aviso no logrotate: {res.stderr.strip()}")
        except FileNotFoundError:
            print("ℹ️ [HOUSEKEEPING] logrotate não instalado no PATH local. Pulando chamada do utilitário.")

    # Remove arquivos de log antigos (.log.1, .log.2.gz, *.log.*, *.gz)
    deleted_files = 0
    cutoff_time = datetime.now().timestamp() - (days * 86400)

    search_patterns = [
        os.path.join(logs_dir, "*.log.*"),
        os.path.join(logs_dir, "*.gz"),
        "/var/log/mosquitto/mosquitto.log.*",
        "/var/log/mosquitto/*.gz"
    ]

    for pattern in search_patterns:
        for filepath in glob.glob(pattern):
            try:
                mtime = os.path.getmtime(filepath)
                if mtime < cutoff_time:
                    if dry_run:
                        print(f"🔍 [DRY-RUN] Arquivo a remover: {filepath}")
                    else:
                        os.remove(filepath)
                        print(f"🗑️ [HOUSEKEEPING] Removido log antigo: {filepath}")
                    deleted_files += 1
            except Exception as e:
                print(f"⚠️ [HOUSEKEEPING] Não foi possível acessar/remover {filepath}: {e}")

    print(f"✅ [HOUSEKEEPING] Limpeza de arquivos de log finalizada ({deleted_files} arquivos removidos).")
    return deleted_files

def check_mosquitto_health(dry_run=False):
    """Verifica e reporta a integridade do diretório de dados e log do Mosquitto."""
    print("🩺 [HOUSEKEEPING] Verificando integridade do Mosquitto persistence...")
    lib_dir = "/var/lib/mosquitto"
    db_file = os.path.join(lib_dir, "mosquitto.db")

    if os.path.exists(lib_dir):
        try:
            stat_info = os.stat(lib_dir)
            print(f"ℹ️ [MOSQUITTO] Diretório {lib_dir} existente (Permissões: {oct(stat_info.st_mode)[-3:]}).")
            if os.path.exists(db_file):
                size_kb = os.path.getsize(db_file) / 1024
                print(f"💾 [MOSQUITTO] Tamanho do mosquitto.db: {size_kb:.2f} KB")
            else:
                print(f"ℹ️ [MOSQUITTO] {db_file} ainda não criado (será gerado pelo autosave).")
        except Exception as e:
            print(f"⚠️ [MOSQUITTO] Erro ao inspecionar {lib_dir}: {e}")
    else:
        print(f"⚠️ [MOSQUITTO] Diretório {lib_dir} não existe!")
        if not dry_run:
            try:
                os.makedirs(lib_dir, exist_ok=True)
                print(f"✅ [MOSQUITTO] Criado diretório {lib_dir}.")
            except Exception as e:
                print(f"❌ [MOSQUITTO] Erro ao criar {lib_dir}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Housekeeping do Light Manager")
    parser.add_argument("--days", type=int, default=7, help="Dias de retenção para eventos e logs (Padrão: 7)")
    parser.add_argument("--dry-run", action="store_true", help="Simula as ações sem remover dados ou alterar arquivos")
    args = parser.parse_args()

    now = datetime.now(SP_TZ)
    print(f"==================================================")
    print(f"🚀 Iniciando Housekeeping Light Manager [{now.strftime('%Y-%m-%d %H:%M:%S %Z')}]")
    if args.dry_run:
        print("⚠️ MODO DRY-RUN ATIVO - Nenhuma alteração real será feita.")
    print(f"==================================================")

    prune_database(days=args.days, dry_run=args.dry_run)
    prune_logs(days=args.days, dry_run=args.dry_run)
    check_mosquitto_health(dry_run=args.dry_run)

    print(f"✅ Housekeeping concluído com sucesso!")
    print(f"==================================================\n")

if __name__ == "__main__":
    main()
