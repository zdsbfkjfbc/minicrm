from app.models import User


def login(client, username='testuser', password='testpass'):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def test_public_register_ignores_role_elevation(client, app):
    response = client.post('/register', data={
        'username': 'novo_usuario',
        'password': 'Senha@123',
        'confirm_password': 'Senha@123',
        'role': 'Gestor',
    }, follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username='novo_usuario').first()
        assert user is not None
        assert user.role == 'Operador'


def test_logout_requires_post(client):
    login(client)
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 405
