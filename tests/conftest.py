"""
Configuração centralizada dos fixtures do Pytest para o Mini CRM.

IMPORTANTE: O fixture 'app' tem scope='session' porque views.py
registra rotas via 'current_app' no momento do import. Se criarmos
múltiplas instâncias de Flask, apenas a primeira terá rotas registradas
(Python cacheia imports de módulo). Por isso, criamos o app UMA VEZ
e resetamos apenas o banco de dados entre cada teste.
"""
import pytest
from app import create_app, db
from app.models import User
from config import Config


class TestConfig(Config):
    """Configuração de testes: banco em memória, CSRF desligado."""
    TESTING = True
    SECRET_KEY = 'test-secret-key-for-pytest'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    REDIS_URL = 'memory://'


@pytest.fixture(scope='session')
def app():
    """Cria a aplicação Flask UMA VEZ por sessão de testes."""
    _app = create_app(TestConfig)
    yield _app


@pytest.fixture(autouse=True)
def reset_db(app):
    """
    Reseta o banco de dados antes de CADA teste.
    Garante isolamento: cada teste começa com uma base limpa + usuário padrão.
    """
    with app.app_context():
        db.drop_all()
        db.create_all()

        user = User(username='testuser', role='Operador')
        user.set_password('testpass')
        db.session.add(user)
        
        admin = User(username='admin', role='Gestor')
        admin.set_password('admin')
        db.session.add(admin)
        
        db.session.commit()

        yield

        db.session.remove()


@pytest.fixture
def client(app):
    """Retorna um test_client pronto para uso."""
    with app.test_client() as c:
        yield c
