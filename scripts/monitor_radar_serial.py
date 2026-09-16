#!/usr/bin/env python3
"""
Monitor Serial Interativo para ESP32-C3 SuperMini + LD2420 Radar
Lê /dev/ttyACM0 a 115200 baud e exibe eventos de transição e telemetria em tempo real.
"""

import sys
import time
import os

try:
    import serial
except ImportError:
    print("❌ Erro: pyserial não instalado. Execute: pip install pyserial")
    sys.exit(1)

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"
BAUD = 115200

# Códigos ANSI para cores
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
WHITE  = "\033[37m"
BG_RED = "\033[41m\033[37m"
BG_GRN = "\033[42m\033[30m"

def main():
    if not os.path.exists(PORT):
        print(f"❌ Porta serial '{PORT}' não encontrada! Verifique a conexão USB do ESP32-C3.")
        sys.exit(1)

    print(f"{BOLD}{CYAN}======================================================{RESET}")
    print(f"{BOLD}{CYAN} 📡 Monitor Serial em Tempo Real - ESP32-C3 Radar     {RESET}")
    print(f"{BOLD}{CYAN} Porta: {PORT} | Baud: {BAUD}                         {RESET}")
    print(f"{BOLD}{CYAN} Pressione Ctrl+C para sair                           {RESET}")
    print(f"{BOLD}{CYAN}======================================================{RESET}\n")

    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
        ser.reset_input_buffer()
    except Exception as e:
        print(f"❌ Falha ao abrir {PORT}: {e}")
        sys.exit(1)

    try:
        while True:
            line_bytes = ser.readline()
            if not line_bytes:
                continue

            line = line_bytes.decode("utf-8", errors="replace").strip()
            if not line:
                continue

            now_str = time.strftime("%H:%M:%S")

            # Formatação contextual por tipo de mensagem
            if "PRESENÇA DETECTADA" in line or "GPIO 2: 1" in line or "HIGH" in line:
                print(f"[{now_str}] {BG_RED} 🏃 {line} {RESET}")
            elif "PRESENÇA CESSADA" in line or "GPIO 2: 0" in line or "LOW" in line:
                print(f"[{now_str}] {GREEN} 🚶 {line} {RESET}")
            elif "[TRANSITION]" in line:
                print(f"[{now_str}] {BOLD}{YELLOW} ⚡ {line} {RESET}")
            elif "[UART_RADAR]" in line:
                print(f"[{now_str}] {CYAN} 📦 {line} {RESET}")
            elif "[TELEMETRIA]" in line:
                print(f"[{now_str}] {WHITE} 📊 {line} {RESET}")
            else:
                print(f"[{now_str}] {line}")

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Monitor serial encerrado pelo usuário.{RESET}")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
