import os
import asyncio
import logging
import json
import base64
import tempfile
import psycopg2
import psutil
import httpx
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from psycopg2 import pool
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# Carrega variáveis
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_ALLOWED_USER_ID", 0))
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# DB Config
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "light_manager")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - BOT - %(message)s')

bot = Bot(token=TOKEN)
dp = Dispatcher()
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Dicionário global para rastrear o estado das luzes em tempo real
light_states = {}

# --- DB Pooling ---

db_pool = pool.ThreadedConnectionPool(
    1, 10,
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    port=DB_PORT
)

def get_db_conn():
    return db_pool.getconn()

def release_db_conn(conn):
    db_pool.putconn(conn)

# --- Auxiliares ---

def check_auth(user_id):
    return user_id == ALLOWED_USER_ID

def get_light_points():
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, mqtt_topic, auto_mode FROM light_points;")
        points = cur.fetchall()
        cur.close()
        return points
    finally:
        release_db_conn(conn)

def get_consumption_report(days):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        query = """
            SELECT p.name, COALESCE(SUM(EXTRACT(EPOCH FROM (next_t - timestamp))/3600), 0) as hours
            FROM (
                SELECT point_id, timestamp, event_type,
                LEAD(timestamp) OVER (PARTITION BY point_id ORDER BY timestamp) as next_t
                FROM light_events
            ) t
            JOIN light_points p ON p.id = t.point_id
            WHERE t.event_type = 'ON' AND t.timestamp > CURRENT_DATE - INTERVAL '%s days'
            GROUP BY p.name;
        """
        cur.execute(query, (days,))
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        release_db_conn(conn)

# --- MQTT ---

def on_mqtt_connect(client, userdata, flags, reason_code, properties):
    logging.info("Conectado ao MQTT Broker")
    points = get_light_points()
    for pt in points:
        client.subscribe(f"{pt[2]}/state")

def on_mqtt_message(client, userdata, msg):
    state = msg.payload.decode()
    topic = msg.topic.replace("/state", "")
    # Atualiza o estado em memória para o comando /status
    light_states[topic] = state
    logging.info(f"Status MQTT: {topic} -> {state}")

mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message

# --- Handlers Telegram ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not check_auth(message.from_user.id): return
    await message.answer(
        "💡 *Light Manager Bot*\n\n"
        "/status - Ver saúde do sistema e luzes\n"
        "/liga - Ligar luzes\n"
        "/desliga - Desligar luzes\n"
        "/relatorio7d - Consumo última semana\n"
        "/relatorio30d - Consumo último mês",
        parse_mode="Markdown"
    )

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    if not check_auth(message.from_user.id): return
    
    # Saúde do Sistema
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    
    # Luzes
    points = get_light_points()
    light_status = ""
    for pt in points:
        mode = "🤖 Auto" if pt[3] else "Manual"
        # Busca o estado atual no dicionário de memória (atualizado via MQTT)
        raw_state = light_states.get(pt[2], "DESCONHECIDO")
        icon = "💡 ON" if raw_state == "ON" else "🌑 OFF"
        light_status += f"• {pt[1]}: {icon} [{mode}]\n"

    status_msg = (
        f"🖥 *Status do Raspberry Pi*\n"
        f"CPU: {cpu}%\n"
        f"RAM: {ram}%\n"
        f"Uptime: {str(uptime).split('.')[0]}\n\n"
        f"💡 *Pontos de Luz*\n"
        f"{light_status if light_status else 'Nenhum cadastrado.'}"
    )
    await message.answer(status_msg, parse_mode="Markdown")

@dp.message(Command("liga"))
async def cmd_liga(message: types.Message):
    if not check_auth(message.from_user.id): return
    points = get_light_points()
    builder = InlineKeyboardBuilder()
    for pt in points:
        builder.button(text=f"💡 {pt[1]}", callback_data=f"mqtt_ON_{pt[2]}")
    builder.adjust(1)
    await message.answer("Escolha qual luz LIGAR:", reply_markup=builder.as_markup())

@dp.message(Command("desliga"))
async def cmd_desliga(message: types.Message):
    if not check_auth(message.from_user.id): return
    points = get_light_points()
    builder = InlineKeyboardBuilder()
    for pt in points:
        builder.button(text=f"🌑 {pt[1]}", callback_data=f"mqtt_OFF_{pt[2]}")
    builder.adjust(1)
    await message.answer("Escolha qual luz DESLIGAR:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("mqtt_"))
async def process_mqtt_callback(callback: types.CallbackQuery):
    if not check_auth(callback.from_user.id): return
    _, action, topic = callback.data.split("_")
    
    # Registra a persistência de override manual e evento no banco
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("SET timezone TO 'America/Sao_Paulo';")
        cur.execute("SELECT id FROM light_points WHERE mqtt_topic = %s", (topic,))
        res = cur.fetchone()
        if res:
            point_id = res[0]
            # Atualiza a coluna manual_override com o novo estado solicitado
            cur.execute(
                "UPDATE light_points SET manual_override = %s WHERE id = %s",
                (action, point_id)
            )
            # Salva o evento como 'manual_control'
            cur.execute(
                "INSERT INTO light_events (point_id, event_type, source, timestamp) VALUES (%s, %s, 'manual_control', NOW())",
                (point_id, action)
            )
            conn.commit()
        cur.close()
    except Exception as e:
        if conn: conn.rollback()
        logging.error(f"Erro ao salvar comando manual do bot no banco: {e}")
    finally:
        if conn: release_db_conn(conn)

    # Garante a entrega do comando via QoS 1
    mqtt_client.publish(f"{topic}/set", action, qos=1)
    await callback.answer(f"Enviado: {action} para {topic}")
    await callback.message.edit_text(f"✅ Comando {action} enviado com sucesso!")

@dp.message(Command("relatorio7d", "relatorio30d"))
async def cmd_relatorio(message: types.Message):
    if not check_auth(message.from_user.id): return
    days = 7 if "7d" in message.text else 30
    report = get_consumption_report(days)
    
    if not report:
        await message.answer(f"Sem dados de consumo para os últimos {days} dias.")
        return

    msg = f"📊 *Relatório de Consumo ({days} dias)*\n\n"
    for name, hours in report:
        msg += f"• *{name}*: {hours:.2f} horas ligada\n"
    
    await message.answer(msg, parse_mode="Markdown")

def execute_light_command(topic, action):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("SET timezone TO 'America/Sao_Paulo';")
        cur.execute("SELECT id FROM light_points WHERE mqtt_topic = %s", (topic,))
        res = cur.fetchone()
        if res:
            point_id = res[0]
            cur.execute("UPDATE light_points SET manual_override = %s WHERE id = %s", (action, point_id))
            cur.execute(
                "INSERT INTO light_events (point_id, event_type, source, timestamp) VALUES (%s, %s, 'voice_control', NOW())",
                (point_id, action)
            )
            conn.commit()
        cur.close()
    except Exception as e:
        if conn: conn.rollback()
        logging.error(f"Erro ao salvar comando de voz no banco: {e}")
    finally:
        if conn: release_db_conn(conn)
        
    mqtt_client.publish(f"{topic}/set", action, qos=1)

@dp.message(F.voice)
async def handle_voice_command(message: types.Message):
    if not check_auth(message.from_user.id): return
    if not GEMINI_API_KEY:
        await message.reply("⚠️ A API do Gemini não está configurada no servidor (falta GEMINI_API_KEY no .env).")
        return
        
    # Feedback visual de processamento
    await message.bot.send_chat_action(chat_id=message.chat.id, action="record_voice")
    
    # Download do arquivo de voz (.ogg)
    file_id = message.voice.file_id
    file_info = await message.bot.get_file(file_id)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
        temp_path = temp_file.name
        
    try:
        await message.bot.download_file(file_info.file_path, temp_path)
        
        with open(temp_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")
            
        prompt = (
            "Você é o assistente de voz do Light Manager. Analise o áudio e responda EXCLUSIVAMENTE "
            "em formato JSON com o seguinte esquema:\n"
            "{\n"
            "  \"action\": \"ON\" | \"OFF\" | \"UNKNOWN\",\n"
            "  \"point_name\": \"frente\" | \"fundos\" | \"todos\" | \"UNKNOWN\"\n"
            "}\n"
            "Identifique se o usuário quer ligar (ON) ou desligar (OFF) e qual área ele mencionou."
        )
        
        headers = {"Content-Type": "application/json"}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "audio/ogg",
                            "data": audio_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            
        if response.status_code != 200:
            raise Exception(f"Erro na API do Gemini: {response.text}")
            
        res_data = response.json()
        model_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(model_text)
        
        action = result.get("action", "UNKNOWN")
        point_name = result.get("point_name", "UNKNOWN")
        
        if action == "UNKNOWN" or point_name == "UNKNOWN":
            await message.reply(
                "❌ Não consegui entender o comando de voz. Tente dizer algo como:\n"
                "- *'Ligar a frente'*\n"
                "- *'Desligar os fundos'*",
                parse_mode="Markdown"
            )
            return
            
        points = get_light_points()
        
        if point_name == "todos":
            for pt in points:
                execute_light_command(pt[2], action)
            await message.reply(f"✅ Comando *{action}* enviado para *TODOS* os pontos!", parse_mode="Markdown")
            return
            
        target_point = None
        for pt in points:
            if point_name in pt[1].lower():
                target_point = pt
                break
                
        if not target_point:
            await message.reply(f"❌ Ponto de luz '{point_name}' não foi encontrado no sistema.")
            return
            
        execute_light_command(target_point[2], action)
        await message.reply(f"✅ Comando *{action}* enviado para *{target_point[1]}*!", parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"Erro ao processar comando de voz: {e}")
        await message.reply("⚠️ Ocorreu um erro interno ao processar seu comando de voz.")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

async def main():
    if MQTT_USER and MQTT_PASS:
        mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        logging.info("🚀 Bot do Telegram iniciado em modo Long Polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"❌ Erro fatal no Bot: {e}")
        await asyncio.sleep(10) # Aguarda antes de deixar o processo morrer para o watchdog agir
        raise e

if __name__ == "__main__":
    asyncio.run(main())
