#!/usr/bin/env python3
# scripts/weather_offset_sync.py

import os
import sys
import logging
from datetime import datetime
import pytz
import psycopg2
from dotenv import load_dotenv
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

# Configuração de Logs para saída padrão (capturado pelo cron)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Carrega as variáveis do .env localizadas no diretório pai
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "light_manager"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

def main():
    logging.info("Iniciando atualização de offsets baseada em cobertura de nuvens...")

    # 1. Obter coordenadas
    try:
        lat = float(os.getenv("LATITUDE", "-24.2839"))
        lon = float(os.getenv("LONGITUDE", "-53.84"))
    except ValueError:
        logging.error("Coordenadas LATITUDE/LONGITUDE inválidas no .env. Usando padrão de Palotina.")
        lat, lon = -24.2839, -53.84

    logging.info(f"Coordenadas para consulta: Latitude {lat}, Longitude {lon}")

    # 2. Configurar cache e cliente Open-Meteo
    cache_path = os.path.join(PROJECT_ROOT, ".openmeteo_cache")
    cache_session = requests_cache.CachedSession(cache_path, expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # 3. Chamar a API Open-Meteo
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "cloud_cover",
        "timezone": "America/Sao_Paulo",
    }

    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
    except Exception as e:
        logging.error(f"Erro ao consultar a API Open-Meteo: {e}")
        sys.exit(1)

    # 4. Processar dados de cobertura de nuvens
    hourly = response.Hourly()
    hourly_cloud_cover = hourly.Variables(0).ValuesAsNumpy()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ).tz_convert(response.Timezone().decode())
    }
    hourly_data["cloud_cover"] = hourly_cloud_cover
    df = pd.DataFrame(data=hourly_data)

    # 5. Encontrar a cobertura de nuvens do horário atual (mais próximo)
    tz = pytz.timezone("America/Sao_Paulo")
    now = datetime.now(tz)
    
    # Adiciona coluna de diferença de tempo e pega o índice de menor diferença
    df['diff'] = (df['date'] - now).abs()
    closest_row = df.loc[df['diff'].idxmin()]
    
    cloud_cover = float(closest_row['cloud_cover'])
    date_matched = closest_row['date']
    
    logging.info(f"Horário atual: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logging.info(f"Previsão mais próxima correspondente: {date_matched.strftime('%Y-%m-%d %H:%M:%S %Z')} com Cloud Cover = {cloud_cover}%")

    # 6. Cálculo dos novos offsets por interpolação linear
    # 0% cover: on = 10, off = -10
    # 100% cover: on = -10, off = 10
    cloud_cover_clamped = max(0.0, min(100.0, cloud_cover))
    offset_on = int(round(10.0 - 0.2 * cloud_cover_clamped))
    offset_off = int(round(-10.0 + 0.2 * cloud_cover_clamped))

    logging.info(f"Valores calculados - Offset Ligar: {offset_on} min | Offset Desligar: {offset_off} min")

    # 7. Atualizar no banco de dados
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Atualiza offset para todos os pontos de luz
        cur.execute(
            "UPDATE light_points SET offset_on_minutes = %s, offset_off_minutes = %s;",
            (offset_on, offset_off)
        )
        updated_rows = cur.rowcount
        conn.commit()
        logging.info(f"Banco de dados atualizado com sucesso! {updated_rows} pontos de luz modificados.")
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao atualizar o banco de dados: {e}")
        sys.exit(1)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
