import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env ANTES de importar a app
load_dotenv()

from app import create_app, db
from app.models import User, Contact

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Contact': Contact}

if __name__ == '__main__':
    app.run(debug=True)
