from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler

import os
import sys
# Adiciona a raiz do projeto ao path para que o Python/Linter encontre o config.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'login'
login.login_message = 'Por favor, faça login para acessar esta página.'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    with app.app_context():
        from datetime import timezone, timedelta

        @app.template_filter('brt')
        def to_brt(dt):
            """Converte datetime UTC para Horário de Brasília (UTC-3) e formata."""
            if not dt:
                return '—'
            BRT = timezone(timedelta(hours=-3))
            dt_brt = dt.replace(tzinfo=timezone.utc).astimezone(BRT)
            return dt_brt.strftime('%d/%m/%Y %H:%M:%S')

        from app import models, views
        
        # Ocultar criação de banco via código para usar migrações
        # db.create_all()  
        
        # Configurar Logging de Produção
        if not app.debug and not app.testing:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/minicrm.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('MiniCRM startup')

    return app
