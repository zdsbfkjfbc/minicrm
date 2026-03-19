#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Verifica se o banco de dados já existe no disco persistente do Render
if [ ! -f /data/app.db ]; then
    echo "Banco de dados não encontrado em /data. Inicializando..."
    python init_db.py
else
    echo "Banco de dados já existe. Pulando inicialização para preservar dados."
    # Opcional: flask db upgrade
fi
