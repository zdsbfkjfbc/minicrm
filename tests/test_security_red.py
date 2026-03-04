"""
Suite de Testes TDD — Fase RED (Devem FALHAR)
Valida vulnerabilidades e regras de negócio que o sistema ainda
não trata de forma adequada segundo o CLAUDE.md:

  1. IDOR: Operador A NÃO deve acessar contatos do Operador B.
     Espera HTTP 403 Forbidden (atualmente devolve 302 redirect).
  2. Data Retroativa: Criar contato com deadline de ontem deve
     ser rejeitado pelo formulário.
  3. XSS no Banco: Tags HTML devem ser removidas ANTES de salvar.
"""
from datetime import date, timedelta
from app.models import User, Contact
from app import db


# ── Helpers ──────────────────────────────────────────────
def login(client, username, password):
    """Helper: autentica o usuário via POST no /login."""
    return client.post('/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)


def _create_operator(username, password):
    """Cria um usuário Operador no banco e retorna o objeto User."""
    user = User(username=username, role='Operador')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


# ═══════════════════════════════════════════════════════════
# TESTE 1 — IDOR (Insecure Direct Object Reference)
# ═══════════════════════════════════════════════════════════
def test_idor_operator_cannot_edit_others_contact(client, app):
    """
    RED — Operador A tenta acessar GET /contact/<id>/edit de um contato
    pertencente ao Operador B.

    Comportamento ESPERADO (seguro):
      → HTTP 403 Forbidden  OU  HTTP 404 Not Found

    Comportamento ATUAL (inseguro):
      → HTTP 302 redirect para /index com flash genérico.
      Isso vaza informação: o atacante sabe que o recurso EXISTE.

    ➜ Este teste DEVE FALHAR até a rota retornar 403/404.
    """
    with app.app_context():
        # Cria Operador B e um contato dele
        op_b = _create_operator('operador_b', 'senhaB123')
        contact_b = Contact(
            customer_name='Cliente Secreto do B',
            status='Aberto',
            deadline=date.today() + timedelta(days=7),
            observations='Dado sigiloso',
            user_id=op_b.id,
        )
        db.session.add(contact_b)
        db.session.commit()
        target_id = contact_b.id

    # Loga como Operador A (testuser, criado pelo fixture)
    login(client, 'testuser', 'testpass')

    # Tenta acessar o contato do Operador B
    response = client.get(
        f'/contact/{target_id}/edit',
        follow_redirects=False,
    )

    assert response.status_code in (403, 404), (
        f"IDOR DETECTADO: Esperava 403/404, mas recebeu {response.status_code}. "
        f"O sistema deveria negar acesso de forma explícita, não redirecionar."
    )


# ═══════════════════════════════════════════════════════════
# TESTE 2 — Data Retroativa (Deadline no Passado)
# ═══════════════════════════════════════════════════════════
def test_reject_past_deadline_returns_error(client):
    """
    RED — Tentar criar um contato com Data Limite = ontem.

    Comportamento ESPERADO:
      → O formulário rejeita com mensagem de validação
        ('não pode ser no passado') e NÃO salva no banco.

    ➜ Este teste falhará se o sistema aceitar datas retroativas.
    """
    login(client, 'testuser', 'testpass')

    yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

    response = client.post('/contact/new', data={
        'customer_name': 'Cliente Data Retroativa',
        'status': 'Aberto',
        'deadline': yesterday,
        'observations': 'Tentativa com data no passado',
    }, follow_redirects=True)

    # Formulário com erro de validação retorna 200 (re-render)
    assert response.status_code == 200

    html = response.data.decode('utf-8')
    assert 'não pode ser no passado' in html, (
        "FALHA: O sistema não exibiu mensagem de validação para data retroativa."
    )

    # Verifica que o contato NÃO foi persistido
    contact = Contact.query.filter_by(
        customer_name='Cliente Data Retroativa'
    ).first()
    assert contact is None, (
        "FALHA: O sistema salvou um contato com deadline no passado!"
    )


# ═══════════════════════════════════════════════════════════
# TESTE 3 — XSS no Banco de Dados (Sanitização de Entrada)
# ═══════════════════════════════════════════════════════════
def test_xss_script_tag_sanitized_before_save(client):
    """
    RED — Enviar <script>alert('hack')</script> no campo observações.

    Comportamento ESPERADO:
      → O dado salvo no banco NÃO contém a tag <script>.
        O texto 'alert('hack')' pode ser preservado (sem tags).

    Diferença importante: sanitizar na entrada (remover tags)
    é mais seguro que confiar apenas no autoescaping do Jinja2,
    pois os dados podem ser exportados via CSV ou APIs futuras.

    ➜ Este teste falhará se <script> for salvo no banco.
    """
    login(client, 'testuser', 'testpass')

    xss_payload = "<script>alert('hack')</script>"

    response = client.post('/contact/new', data={
        'customer_name': 'Cliente XSS Test',
        'status': 'Aberto',
        'deadline': date.today().strftime('%Y-%m-%d'),
        'observations': xss_payload,
    }, follow_redirects=True)

    assert response.status_code == 200

    contact = Contact.query.filter_by(
        customer_name='Cliente XSS Test'
    ).first()
    assert contact is not None, (
        "O contato não foi criado — erro inesperado."
    )

    # A tag <script> NÃO deve estar presente no banco
    assert '<script>' not in (contact.observations or ''), (
        "XSS DETECTADO: A tag <script> foi salva no banco de dados "
        "sem sanitização! Dados poluídos podem ser explorados em "
        "exportações CSV e APIs REST futuras."
    )

    # O conteúdo textual deve sobreviver (apenas tags removidas)
    assert 'alert' in (contact.observations or ''), (
        "O sanitizador removeu conteúdo demais — "
        "deveria preservar o texto e remover apenas as tags HTML."
    )
