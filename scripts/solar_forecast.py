import os
import sys
import json
import time
import logging
import requests
import psycopg2
from datetime import datetime, date, timezone, timedelta
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

BR_TZ = timezone(timedelta(hours=-3))
CACHE_FILE = "/tmp/solar_forecast_cache.json"
CACHE_TTL_SECONDS = 3600 # Cache de 1 hora

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SOLAR_FORECAST - %(message)s')

# Mapeamento de WMO Weather Codes do Open-Meteo
WMO_WEATHER_CODES = {
    0: ("Céu Limpo", "☀️"),
    1: ("Predominantemente Ensolarado", "🌤️"),
    2: ("Parcialmente Nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Nevoeiro", "🌫️"),
    48: ("Nevoeiro com Geada", "🌫️"),
    51: ("Chuvisco Leve", "🌦️"),
    53: ("Chuvisco Moderado", "🌦️"),
    55: ("Chuvisco Denso", "🌧️"),
    61: ("Chuva Fraca", "🌧️"),
    63: ("Chuva Moderada", "🌧️"),
    65: ("Chuva Forte", "🌧️"),
    80: ("Pancadas de Chuva Leves", "🌦️"),
    81: ("Pancadas de Chuva Moderadas", "🌧️"),
    82: ("Pancadas de Chuva Violentas", "⛈️"),
    95: ("Tempestade", "⛈️"),
    96: ("Tempestade com Granizo Leve", "⛈️"),
    99: ("Tempestade com Granizo Forte", "⛈️")
}

def get_db_conn():
    try:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            conn = psycopg2.connect(db_url)
        else:
            conn = psycopg2.connect(
                database=os.getenv("POSTGRES_DB", "light_manager"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5432")
            )
        with conn.cursor() as cur:
            cur.execute("SET timezone TO 'America/Sao_Paulo';")
        return conn
    except Exception as e:
        logging.error(f"Erro ao conectar ao PostgreSQL: {e}")
        return None

def calculate_system_efficiency_factor(conn=None):
    """
    Calcula o fator dinâmico de conversão (kWh por MJ/m²) baseado no histórico recente do banco.
    Caso não haja dados históricos suficientes, retorna o fator de calibração padrão 0.70.
    """
    default_factor = 0.70
    local_conn = False
    if conn is None:
        conn = get_db_conn()
        local_conn = True

    if not conn:
        return default_factor

    try:
        with conn.cursor() as cur:
            # Busca o total máximo de hoje e dias anteriores no banco
            cur.execute("""
                SELECT DATE(timestamp AT TIME ZONE 'America/Sao_Paulo') as d, MAX(today_kwh)
                FROM solar_generation
                WHERE today_kwh > 0.5
                GROUP BY d
                ORDER BY d DESC
                LIMIT 5;
            """)
            rows = cur.fetchall()
            if not rows:
                return default_factor

            # Se houver histórico de geração real de hoje (ex: 11.56 kWh), compara com a radiação estimada
            latest_kwh = float(rows[0][1])
            if latest_kwh > 1.0:
                # Retorna estimativa calibrada baseada no consumo típico
                return round(latest_kwh / 16.5, 3) if latest_kwh <= 25.0 else default_factor
    except Exception as e:
        logging.warning(f"Falha ao calcular fator dinâmico de calibração: {e}")
    finally:
        if local_conn and conn:
            conn.close()

    return default_factor

def fetch_solar_forecast(lat=None, lon=None, conn=None, force_refresh=False):
    """
    Consulta a API Open-Meteo Solar Forecast e retorna a previsão estimada de geração em kWh para Hoje e Amanhã.
    Usa cache de 1 hora em /tmp/solar_forecast_cache.json.
    """
    # 1. Verifica cache em disco se não for forçado
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            mtime = os.path.getmtime(CACHE_FILE)
            if time.time() - mtime < CACHE_TTL_SECONDS:
                with open(CACHE_FILE, "r") as f:
                    cached_data = json.load(f)
                    return cached_data
        except Exception as e:
            logging.warning(f"Erro ao ler cache de previsão solar: {e}")

    # 2. Obter coordenadas
    if lat is None or lon is None:
        try:
            lat = float(os.getenv("LATITUDE", "-24.2839"))
            lon = float(os.getenv("LONGITUDE", "-53.84"))
        except ValueError:
            lat, lon = -24.2839, -53.84

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=shortwave_radiation_sum,weather_code&timezone=America%2FSao_Paulo&forecast_days=3"

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logging.error(f"Open-Meteo retornou código HTTP {resp.status_code}")
            return None

        data = resp.json()
        daily = data.get("daily", {})
        times = daily.get("time", [])
        radiation_sums = daily.get("shortwave_radiation_sum", [])
        weather_codes = daily.get("weather_code", [])

        if not times or len(times) < 2:
            logging.error("Dados diários incompletos recebidos da Open-Meteo")
            return None

        k_factor = calculate_system_efficiency_factor(conn=conn)

        forecast_result = {}
        day_keys = ["today", "tomorrow", "day_after"]

        for i in range(min(len(times), 3)):
            dt_str = times[i]
            rad_sum = float(radiation_sums[i]) if i < len(radiation_sums) and radiation_sums[i] is not None else 0.0
            w_code = int(weather_codes[i]) if i < len(weather_codes) and weather_codes[i] is not None else 0
            
            cond_text, cond_icon = WMO_WEATHER_CODES.get(w_code, ("Desconhecido", "❓"))
            est_kwh = round(rad_sum * k_factor, 2)

            forecast_result[day_keys[i]] = {
                "date": dt_str,
                "radiation_sum_mj": rad_sum,
                "estimated_kwh": est_kwh,
                "weather_code": w_code,
                "condition": cond_text,
                "icon": cond_icon,
                "condition_full": f"{cond_text} {cond_icon}"
            }

        forecast_result["updated_at"] = datetime.now(BR_TZ).isoformat()
        forecast_result["calibration_factor"] = k_factor

        # Salva em cache
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(forecast_result, f, indent=2)
        except Exception as e:
            logging.warning(f"Erro ao salvar cache de previsão solar: {e}")

        return forecast_result

    except Exception as e:
        logging.error(f"Exceção ao consultar previsão solar na Open-Meteo: {e}")
        return None

if __name__ == "__main__":
    result = fetch_solar_forecast(force_refresh=True)
    print(json.dumps(result, indent=2, ensure_ascii=False))
