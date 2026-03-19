import pytest
from datetime import date, timedelta
from app.models import Contact, AuditLog, User
from app import db

def login(client, username='admin', password='admin'):
    """Helper: autentica o usuário."""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)

def test_contact_creation_and_audit(client):
    """Verifica se a criação de um contato gera um log de auditoria."""
    login(client, 'admin', 'admin')
    
    response = client.post('/contact/new', data={
        'contact_type': 'Pessoa',
        'customer_name': 'Cliente Audit Test',
        'status': 'Aberto',
        'deadline': date.today().strftime('%Y-%m-%d'),
        'observations': 'Teste de auditoria'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    contact = Contact.query.filter_by(customer_name='Cliente Audit Test').first()
    assert contact is not None
    
    # Verifica AuditLog
    audit = AuditLog.query.filter_by(target_id=contact.id, action='criou').first()
    assert audit is not None
    assert audit.target_type == 'Contact'

def test_index_filtering_by_status(client):
    """Verifica o filtro de status na listagem."""
    login(client, 'admin', 'admin')
    
    # Cria contatos com diferentes status
    c1 = Contact(customer_name='Aberto 1', status='Aberto', user_id=1)
    c2 = Contact(customer_name='Resolvido 1', status='Resolvido', user_id=1)
    db.session.add_all([c1, c2])
    db.session.commit()
    
    # Filtra por Aberto
    response = client.get('/index?status=Aberto')
    html = response.data.decode('utf-8')
    assert 'Aberto 1' in html
    assert 'Resolvido 1' not in html

def test_index_search(client):
    """Verifica a busca por nome no index."""
    login(client, 'admin', 'admin')
    
    c = Contact(customer_name='Busca Unica', status='Aberto', user_id=1)
    db.session.add(c)
    db.session.commit()
    
    response = client.get('/index?search=Busca')
    html = response.data.decode('utf-8')
    assert 'Busca Unica' in html
    
    response = client.get('/index?search=NaoExiste')
    html = response.data.decode('utf-8')
    assert 'Busca Unica' not in html

def test_role_visibility_logic(client):
    """Verifica se o Operador vê apenas seus contatos e o Gestor vê todos."""
    # Gestor (ID 2 de acordo com conftest) cria um contato
    login(client, 'admin', 'admin')
    client.post('/contact/new', data={
        'contact_type': 'Pessoa',
        'customer_name': 'Contato do Admin',
        'status': 'Aberto',
        'deadline': date.today().strftime('%Y-%m-%d'),
        'observations': '...'
    })
    
    # Logout e Login como testuser (Operador, ID 1)
    client.post('/logout', follow_redirects=True)
    login(client, 'testuser', 'testpass')
    
    # testuser cria seu próprio contato
    client.post('/contact/new', data={
        'contact_type': 'Pessoa',
        'customer_name': 'Contato do TestUser',
        'status': 'Aberto',
        'deadline': date.today().strftime('%Y-%m-%d'),
        'observations': '...'
    })
    
    # testuser não deve ver o contato do admin
    response = client.get('/index')
    html = response.data.decode('utf-8')
    assert 'Contato do TestUser' in html
    assert 'Contato do Admin' not in html
    
    # Logout e Login como Admin novamente
    client.post('/logout', follow_redirects=True)
    login(client, 'admin', 'admin')
    
    # Gestor deve ver ambos
    response = client.get('/index')
    html = response.data.decode('utf-8')
    assert 'Contato do TestUser' in html
    assert 'Contato do Admin' in html

def test_dashboard_metrics_gestor_only(client):
    """Verifica acesso ao dashboard e cálculo de métricas."""
    # Tenta acessar como Operador
    login(client, 'testuser', 'testpass')
    response = client.get('/dashboard', follow_redirects=True)
    assert 'Acesso negado' in response.data.decode('utf-8')
    
    # Acessa como Gestor
    client.post('/logout', follow_redirects=True)
    login(client, 'admin', 'admin')
    response = client.get('/dashboard')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'Métricas' in html
    assert 'Total' in html
