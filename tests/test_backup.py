import os
import subprocess
from dotenv import load_dotenv

# Carrega variáveis para o teste
load_dotenv()

def test_backup_script_requirements():
    """Valida se as dependências do script de backup estão presentes no sistema."""
    # 1. Verifica rclone
    try:
        res = subprocess.run(["rclone", "--version"], capture_output=True)
        assert res.returncode == 0, "Rclone não está instalado ou funcional."
    except FileNotFoundError:
        assert False, "Binário 'rclone' não encontrado no PATH."

    # 2. Verifica docker (necessário para o pg_dump)
    try:
        res = subprocess.run(["docker", "--version"], capture_output=True)
        assert res.returncode == 0, "Docker não está instalado."
    except FileNotFoundError:
        assert False, "Binário 'docker' não encontrado no PATH."

def test_r2_env_vars():
    """Garante que todas as variáveis necessárias para o backup no R2 estão no .env"""
    required_vars = [
        "R2_ACCESS_KEY_ID", 
        "R2_SECRET_ACCESS_KEY", 
        "R2_BUCKET_NAME", 
        "R2_ENDPOINT_URL"
    ]
    for var in required_vars:
        value = os.getenv(var)
        assert value is not None and value != "", f"Variável {var} ausente no .env"
