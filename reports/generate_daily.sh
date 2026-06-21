#!/bin/bash
# reports/generate_daily.sh
# Ativa o ambiente virtual e executa a geração de relatório diário

DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$DIR/.."
cd "$PROJECT_ROOT"

source .venv/bin/activate
python3 reports/generate_daily.py
