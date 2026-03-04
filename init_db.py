import os
from datetime import date, timedelta
from app import create_app, db
from app.models import User, Contact

app = create_app()

with app.app_context():
    print("Recriando o banco de dados...")
    db.drop_all()
    db.create_all()

    print("Criando usuário 'admin' padrão (Gestor)...")
    admin = User(username='admin', role='Gestor')
    admin.set_password('admin')
    db.session.add(admin)

    print("Criando usuário 'operador1' padrão...")
    op = User(username='operador1', role='Operador')
    op.set_password('1234')
    db.session.add(op)
    db.session.commit()

    print("Criando dados de exemplo...")
    today = date.today()
    c1 = Contact(customer_name='Empresa Solar', status='Aberto', deadline=today + timedelta(days=2), observations='Interesse no produto.', owner=admin)
    c2 = Contact(customer_name='João Silva', status='Aguardando Cliente', deadline=today - timedelta(days=1), observations='Aguardando envio de docs.', owner=op)
    c3 = Contact(customer_name='Tech Solutions', status='Resolvido', deadline=today, observations='Fechado.', owner=op)
    
    db.session.add_all([c1, c2, c3])
    db.session.commit()

    print("Banco de dados atualizado com sucesso!")
