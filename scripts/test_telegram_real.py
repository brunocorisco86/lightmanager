import os
import sys
import logging
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para importar o solar_worker
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.solar_worker import send_telegram_message

# Carrega variáveis
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - TEST - %(message)s')

def test_real_notification():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    user_id = os.getenv("TELEGRAM_ALLOWED_USER_ID")
    
    print("\n--- 🚀 Teste de Notificação Real Light Manager ---")
    
    if not token or not user_id:
        print("❌ ERRO: TELEGRAM_BOT_TOKEN ou TELEGRAM_ALLOWED_USER_ID não encontrados no .env")
        return

    print(f"📡 Tentando enviar mensagem para o User ID: {user_id}")
    
    msg = (
        "🔔 *Teste de Sistema*\n\n"
        "O sistema de mensagens do *Light Manager* está sendo testado.\n\n"
        "✅ Se você recebeu esta mensagem, significa que as notificações de gatilho solar estão configuradas corretamente e prontas para o uso!"
    )
    
    try:
        send_telegram_message(msg)
        print("✅ Comando de envio executado! Verifique seu Telegram.")
        print("Nota: Se a mensagem NÃO chegou, verifique se você iniciou o bot no Telegram dando um /start.")
    except Exception as e:
        print(f"❌ Falha crítica ao tentar rodar o teste: {e}")

if __name__ == "__main__":
    test_real_notification()
