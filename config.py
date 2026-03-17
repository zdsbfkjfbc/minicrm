import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY and 'pytest' not in sys.modules:
        raise RuntimeError("A variável de ambiente SECRET_KEY é obrigatória para executar a aplicação.")
    elif not SECRET_KEY:
        SECRET_KEY = 'test-key-for-pytest'
        
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    WEBHOOK_TOKEN = os.environ.get('WEBHOOK_TOKEN', 'minicrm-hook')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 2 * 1024 * 1024))
    
    # Hardening de Cookies de Sessão
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # Requer HTTPS em produção
    SESSION_COOKIE_SAMESITE = 'Lax'
