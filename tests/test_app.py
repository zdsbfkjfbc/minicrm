"""
Suite de Testes TDD — Mini CRM
Testa Edge Cases de segurança e validação:
  1. Data de retorno no passado (Validação de negócio)
  2. Injeção XSS nos campos de observação (Sanitização)
  3. Acesso não-autenticado a rotas protegidas (Controle de acesso)
"""
from datetime import date, timedelta
from app.models import Contact
from app import db


def login(client, username='testuser', password='testpass'):
    """Helper: autentica o usuário via POST no /login."""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


# ──────────────────────────────────────────────
# Teste 1: Acesso não-autenticado
# ──────────────────────────────────────────────
def test_unauthenticated_edit_redirects_to_login(client):
    """
    Acessar /contact/<id>/edit sem estar logado
    deve redirecionar para /login (HTTP 302).
    """
    response = client.get('/contact/1/edit', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers.get('Location', '')


def test_unauthenticated_new_contact_redirects(client):
    """
    Acessar /contact/new sem estar logado
    deve redirecionar para /login (HTTP 302).
    """
    response = client.get('/contact/new', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers.get('Location', '')


# ──────────────────────────────────────────────
# Teste 2: Data de retorno no passado
# ──────────────────────────────────────────────
def test_reject_past_deadline(client):
    """
    Tentar salvar um contato com Data Limite no passado.
    O WTForms deve rejeitar via validate_deadline e recarregar
    o formulário (HTTP 200) sem criar o registro no banco.
    """
    login(client)

    past_date = (date.today() - timedelta(days=5)).strftime('%Y-%m-%d')
    response = client.post('/contact/new', data={
        'customer_name': 'Cliente Passado',
        'status': 'Aberto',
        'deadline': past_date,
        'observations': 'Teste data passada'
    }, follow_redirects=True)

    # WTForms recarrega o formulário com status 200 quando há erro
    assert response.status_code == 200

    # Verifica se a mensagem de validação está na resposta HTML
    html = response.data.decode('utf-8')
    assert 'não pode ser no passado' in html

    # Garante que o contato NÃO foi salvo no banco
    contact = Contact.query.filter_by(customer_name='Cliente Passado').first()
    assert contact is None, \
        "FALHA: O sistema salvou um contato com data no passado!"


def test_accept_today_deadline(client):
    """
    Salvar um contato com Data Limite = hoje deve ser aceito.
    Isso garante que o validador não bloqueia datas válidas.
    """
    login(client)

    today = date.today().strftime('%Y-%m-%d')
    response = client.post('/contact/new', data={
        'customer_name': 'Cliente Hoje',
        'status': 'Aberto',
        'deadline': today,
        'observations': 'Teste data de hoje'
    }, follow_redirects=True)

    # Após criação bem-sucedida, redireciona para /index (200 após follow)
    assert response.status_code == 200

    contact = Contact.query.filter_by(customer_name='Cliente Hoje').first()
    assert contact is not None, \
        "FALHA: O sistema rejeitou um contato com data de hoje!"


# ──────────────────────────────────────────────
# Teste 3: Injeção XSS nas observações
# ──────────────────────────────────────────────
def test_xss_sanitized_in_observations(client):
    """
    Enviar <script>alert('XSS')</script> no campo de observações.
    O sistema deve sanitizar e gravar sem a tag <script>.
    """
    login(client)

    xss_payload = '<script>alert("XSS")</script>'
    response = client.post('/contact/new', data={
        'customer_name': 'Cliente XSS',
        'status': 'Aberto',
        'deadline': date.today().strftime('%Y-%m-%d'),
        'observations': xss_payload
    }, follow_redirects=True)

    assert response.status_code == 200

    contact = Contact.query.filter_by(customer_name='Cliente XSS').first()
    assert contact is not None, \
        "FALHA: O contato não foi criado!"
    assert '<script>' not in (contact.observations or ''), \
        "FALHA: Tag <script> foi salva no banco sem sanitização!"
    # Verifica que o conteúdo de texto foi preservado (só a tag removida)
    assert 'alert' in (contact.observations or ''), \
        "FALHA: O sanitizador removeu conteúdo demais!"


def test_xss_img_onerror_sanitized(client):
    """
    Enviar tag <img onerror=...> no campo de observações.
    O sistema deve remover a tag HTML.
    """
    login(client)

    xss_payload = '<img src=x onerror=alert(1)>'
    response = client.post('/contact/new', data={
        'customer_name': 'Cliente IMG XSS',
        'status': 'Aberto',
        'deadline': date.today().strftime('%Y-%m-%d'),
        'observations': xss_payload
    }, follow_redirects=True)

    assert response.status_code == 200

    contact = Contact.query.filter_by(customer_name='Cliente IMG XSS').first()
    assert contact is not None
    assert '<img' not in (contact.observations or ''), \
        "FALHA: Tag <img> foi salva no banco sem sanitização!"
