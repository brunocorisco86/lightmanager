import os
import csv
import re
import unicodedata
import requests
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Carrega variáveis
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "light_manager")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

def create_table_if_not_exists(cur):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS energy_tariffs (
            id SERIAL PRIMARY KEY,
            distribuidora VARCHAR(150) NOT NULL,
            slug VARCHAR(150) UNIQUE NOT NULL,
            estado VARCHAR(2) NOT NULL,
            cnpj VARCHAR(25),
            tarifa_energia_kwh NUMERIC(10, 6) NOT NULL,
            tarifa_uso_kwh NUMERIC(10, 6),
            modalidade VARCHAR(100),
            subgrupo VARCHAR(50),
            inicio_vigencia DATE,
            fim_vigencia DATE,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    ''')

def get_csv_url():
    print("🔍 Buscando link do CSV no portal de dados abertos da ANEEL...")
    api_url = "https://dadosabertos.aneel.gov.br/api/3/action/package_show"
    res = requests.get(api_url, params={"id": "tarifas-distribuidoras-energia-eletrica"}, timeout=15)
    res.raise_for_status()
    data = res.json()
    resources = data.get("result", {}).get("resources", [])
    csv_resource = next((r for r in resources if r.get("format", "").upper() == "CSV"), None)
    if not csv_resource:
        raise ValueError("Nenhum recurso CSV encontrado nos metadados da ANEEL.")
    return csv_resource.get("url")

def sync():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        create_table_if_not_exists(cur)
        conn.commit()
        
        csv_url = get_csv_url()
        print(f"📥 Baixando e processando tarifas de: {csv_url}")
        
        # Faz streaming da resposta para não estourar a memória RAM
        res = requests.get(csv_url, stream=True, timeout=30)
        res.raise_for_status()
        
        # Detecta encoding se possível, ou usa utf-8/latin-1
        encoding = res.encoding if res.encoding else 'utf-8'
        if encoding.lower() == 'iso-8859-1':
            encoding = 'latin-1'
            
        print(f"⚙️ Lendo dados CSV com encoding: {encoding}...")
        
        lines = (line.decode(encoding, errors='replace') for line in res.iter_lines())
        reader = csv.DictReader(lines, delimiter=';')
        
        count = 0
        tariffs_to_save = {}
        
        for row in reader:
            classe = row.get("DscClasse")
            subgrupo = row.get("DscSubGrupo")
            modalidade = row.get("DscModalidadeTarifaria")
            
            # Filtros principais: classe residencial e subgrupo B1 (convencional)
            if classe == 'Residencial' and subgrupo == 'B1' and modalidade == 'Convencional':
                agente = row.get("SigAgente")
                vlr_te = row.get("VlrTE")
                vlr_tusd = row.get("VlrTUSD")
                
                if agente and vlr_te:
                    # Gera o slug normalizado compatível com o da API em JS
                    slug = agente.lower().strip()
                    slug = re.sub(r'\s+', '-', slug)
                    slug = ''.join(c for c in unicodedata.normalize('NFD', slug) if unicodedata.category(c) != 'Mn')
                    slug = re.sub(r'[^a-z0-9\-]', '', slug)
                    
                    try:
                        te = float(vlr_te.replace(',', '.')) / 1000.0
                        tusd = float(vlr_tusd.replace(',', '.')) / 1000.0 if vlr_tusd else 0.0
                    except ValueError:
                        continue
                        
                    inicio = row.get("DatInicioVigencia")
                    fim = row.get("DatFimVigencia")
                    
                    try:
                        dt_inicio = datetime.strptime(inicio, "%Y-%m-%d").date() if inicio else None
                        dt_fim = datetime.strptime(fim, "%Y-%m-%d").date() if fim else None
                    except ValueError:
                        dt_inicio = None
                        dt_fim = None
                        
                    uf = row.get("SigUF", "BR")
                    cnpj = row.get("NumCNPJDistribuidora")
                    
                    # Mantém apenas o registro com vigência mais recente para cada distribuidora
                    if slug in tariffs_to_save:
                        existing = tariffs_to_save[slug]
                        if dt_inicio and existing['inicio_vigencia'] and dt_inicio > existing['inicio_vigencia']:
                            tariffs_to_save[slug] = {
                                "distribuidora": agente,
                                "estado": uf,
                                "cnpj": cnpj,
                                "tarifa_energia_kwh": te,
                                "tarifa_uso_kwh": tusd,
                                "modalidade": modalidade,
                                "subgrupo": subgrupo,
                                "inicio_vigencia": dt_inicio,
                                "fim_vigencia": dt_fim
                            }
                    else:
                        tariffs_to_save[slug] = {
                            "distribuidora": agente,
                            "estado": uf,
                            "cnpj": cnpj,
                            "tarifa_energia_kwh": te,
                            "tarifa_uso_kwh": tusd,
                            "modalidade": modalidade,
                            "subgrupo": subgrupo,
                            "inicio_vigencia": dt_inicio,
                            "fim_vigencia": dt_fim
                        }
        
        print(f"💾 Salvando {len(tariffs_to_save)} tarifas no banco de dados...")
        for slug, data in tariffs_to_save.items():
            cur.execute(
                """
                INSERT INTO energy_tariffs (
                    distribuidora, slug, estado, cnpj, 
                    tarifa_energia_kwh, tarifa_uso_kwh, 
                    modalidade, subgrupo, inicio_vigencia, fim_vigencia, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (slug) DO UPDATE SET
                    distribuidora = EXCLUDED.distribuidora,
                    estado = EXCLUDED.estado,
                    cnpj = EXCLUDED.cnpj,
                    tarifa_energia_kwh = EXCLUDED.tarifa_energia_kwh,
                    tarifa_uso_kwh = EXCLUDED.tarifa_uso_kwh,
                    modalidade = EXCLUDED.modalidade,
                    subgrupo = EXCLUDED.subgrupo,
                    inicio_vigencia = EXCLUDED.inicio_vigencia,
                    fim_vigencia = EXCLUDED.fim_vigencia,
                    updated_at = NOW();
                """,
                (
                    data["distribuidora"], slug, data["estado"], data["cnpj"],
                    data["tarifa_energia_kwh"], data["tarifa_uso_kwh"],
                    data["modalidade"], data["subgrupo"], data["inicio_vigencia"], data["fim_vigencia"]
                )
            )
            count += 1
            
        conn.commit()
        print(f"✅ Sincronização concluída! {count} tarifas inseridas/atualizadas no banco.")
        
    except Exception as e:
        print(f"❌ Erro ao sincronizar tarifas da ANEEL: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    sync()
