#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Inicializa o banco de dados (sempre no free tier do Render, pois o disco é efêmero)
echo "Limpando e Inicializando banco de dados no Free Tier..."
python init_db.py
