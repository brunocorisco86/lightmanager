import os
import psycopg2
import requests
from datetime import datetime, date
from dotenv import load_dotenv

# Load environment variables
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "light_manager")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

DISTRIBUTOR_SLUG = os.getenv("ENERGY_DISTRIBUTOR_SLUG")
try:
    TAX_RATE = float(os.getenv("ENERGY_TAX_RATE", "0.0"))
except ValueError:
    TAX_RATE = 0.0

def main():
    if not TG_TOKEN or not TG_USER_ID:
        print("Configuration error: TELEGRAM_BOT_TOKEN or TELEGRAM_ALLOWED_USER_ID not found in environment.")
        return

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()
        
        # Seta o timezone correto na sessão para que NOW() e CURRENT_DATE usem fuso horário local
        cur.execute("SET timezone TO 'America/Sao_Paulo';")
        
        # Consulta avançada de sobreposição para calcular o tempo total ativo de cada lâmpada "hoje"
        query = """
            SELECT p.name, p.power_w,
                   COALESCE(SUM(EXTRACT(EPOCH FROM (
                       GREATEST(
                           INTERVAL '0 seconds',
                           LEAST(COALESCE(next_t, NOW()), NOW()) - GREATEST(timestamp, CURRENT_DATE)
                       )
                   ))/3600), 0) as hours
            FROM (
                SELECT point_id, timestamp, event_type,
                LEAD(timestamp) OVER (PARTITION BY point_id ORDER BY timestamp) as next_t
                FROM light_events
            ) t
            JOIN light_points p ON p.id = t.point_id
            WHERE t.event_type = 'ON'
              AND timestamp < NOW()
              AND COALESCE(next_t, NOW()) >= CURRENT_DATE
            GROUP BY p.name, p.power_w
            ORDER BY p.name;
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        # Consulta de tarifas se a distribuidora estiver configurada
        tarifa_kwh = 0.0
        dist_name = None
        if DISTRIBUTOR_SLUG:
            cur.execute(
                "SELECT distribuidora, tarifa_energia_kwh, tarifa_uso_kwh FROM energy_tariffs WHERE slug = %s",
                (DISTRIBUTOR_SLUG.lower().strip(),)
            )
            t_res = cur.fetchone()
            if t_res:
                dist_name = t_res[0]
                te = float(t_res[1])
                tusd = float(t_res[2]) if t_res[2] else 0.0
                tarifa_kwh = (te + tusd) * (1.0 + TAX_RATE)

        cur.close()
        conn.close()

        today_str = date.today().strftime("%d/%m/%Y")
        
        if not rows or all(hours == 0 for _, _, hours in rows):
            msg = f"📊 *Relatório Diário de Consumo* ({today_str})\n\nNenhuma lâmpada foi ligada hoje."
        else:
            msg = f"📊 *Relatório Diário de Consumo* ({today_str})\n\n"
            total_kwh = 0.0
            total_cost = 0.0
            for name, power_w, hours in rows:
                hours_f = float(hours)
                if hours_f <= 0.01:
                    continue
                kwh = (hours_f * float(power_w)) / 1000.0
                total_kwh += kwh
                
                if tarifa_kwh > 0:
                    cost = kwh * tarifa_kwh
                    total_cost += cost
                    msg += f"• *{name}*: {hours_f:.2f}h ligada (Est: {kwh:.3f} kWh | R$ {cost:.2f})\n"
                else:
                    msg += f"• *{name}*: {hours_f:.2f}h ligada (Est: {kwh:.3f} kWh)\n"
            
            if total_kwh > 0:
                if tarifa_kwh > 0:
                    msg += f"\n🔋 *Total Geral Estimado*: {total_kwh:.3f} kWh (R$ {total_cost:.2f})"
                    msg += f"\n⚡ _Tarifa baseada na distribuidora: {dist_name}_"
                else:
                    msg += f"\n🔋 *Total Geral Estimado*: {total_kwh:.3f} kWh"
            else:
                msg += "\n🔋 Nenhuma lâmpada ativa por tempo significativo."

        # Envia a mensagem para o bot com tratamento de Rate-Limit e retentativas
        import time
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {
            "chat_id": TG_USER_ID,
            "text": msg,
            "parse_mode": "Markdown"
        }
        
        for attempt in range(3):
            try:
                res = requests.post(url, json=payload, timeout=10)
                if res.status_code == 200:
                    print("Daily report sent successfully to Telegram.")
                    break
                elif res.status_code == 429:
                    try:
                        retry_after = res.json().get("parameters", {}).get("retry_after", 5)
                    except Exception:
                        retry_after = 5
                    print(f"Warning: Rate Limit (429) no Telegram. Aguardando {retry_after}s...")
                    time.sleep(retry_after)
                else:
                    print(f"Error sending report to Telegram: HTTP {res.status_code} - {res.text}")
                    break
            except Exception as e:
                print(f"Error connecting to Telegram (attempt {attempt + 1}/3): {e}")
                time.sleep(2)

    except Exception as e:
        print(f"Error executing daily report script: {e}")

if __name__ == "__main__":
    main()
