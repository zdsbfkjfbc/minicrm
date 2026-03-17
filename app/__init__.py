import json
import logging
import os
import sys
import uuid
from logging.handlers import RotatingFileHandler

from flask import Flask, g, jsonify, request
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

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
        from app.forms import LogoutForm

        class JSONFormatter(logging.Formatter):
            def format(self, record):
                trace_id = getattr(record, 'trace_id', g.get('trace_id', None) if 'g' in globals() else None)
                payload = {
                    'time': self.formatTime(record, self.datefmt),
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'logger': record.name,
                    'trace_id': trace_id,
                }
                if record.exc_info:
                    payload['exception'] = self.formatException(record.exc_info)
                return json.dumps(payload, default=str)

        @app.template_filter('brt')
        def to_brt(dt):
            """Converte datetime UTC para Horário de Brasília (UTC-3) e formata."""
            if not dt:
                return '—'
            BRT = timezone(timedelta(hours=-3))
            dt_brt = dt.replace(tzinfo=timezone.utc).astimezone(BRT)
            return dt_brt.strftime('%d/%m/%Y %H:%M:%S')

        @app.context_processor
        def inject_logout_form():
            return {'logout_form': LogoutForm()}

        @app.before_request
        def attach_trace_id():
            trace_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
            g.trace_id = trace_id

        @app.after_request
        def add_header(response):
            response.headers['X-Request-ID'] = getattr(g, 'trace_id', '')
            return response

        from app import models, views
        from app.api.v1.contacts import bp as api_v1_bp
        app.register_blueprint(api_v1_bp)

        # Logging de Produção estruturado
        if not app.debug and not app.testing:
            formatter = JSONFormatter()
            console_handler = RotatingFileHandler('logs/minicrm.log', maxBytes=10240, backupCount=10)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)
            app.logger.addHandler(console_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('MiniCRM startup')

    @app.route('/healthz')
    def healthz():
        return jsonify({'status': 'ok', 'trace_id': getattr(g, 'trace_id', '')})

    return app
