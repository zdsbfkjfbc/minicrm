from datetime import datetime, date, timezone
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='Operador') # 'Operador' ou 'Gestor'
    contacts = db.relationship('Contact', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(128), index=True, nullable=False)
    contact_type  = db.Column(db.String(10), default='Pessoa')  # 'Pessoa' ou 'Empresa'
    email         = db.Column(db.String(120), nullable=True)
    phone         = db.Column(db.String(20),  nullable=True)
    status = db.Column(db.String(64), index=True, default='Aberto')
    deadline = db.Column(db.Date, nullable=True)
    observations = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Contact {self.customer_name}>'

    def is_overdue(self):
        if self.deadline and self.status != 'Resolvido':
            return date.today() > self.deadline
        return False

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, index=True, nullable=False)
    value = db.Column(db.String(256), nullable=False)
    description = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        return f'<SystemSetting {self.key}={self.value}>'

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(64), nullable=False)
    target_type = db.Column(db.String(64), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.user_id} {self.action} {self.target_type} {self.target_id}>'
