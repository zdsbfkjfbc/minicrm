from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (BooleanField, DateField, IntegerField, PasswordField,
                     SelectField, StringField, SubmitField, TextAreaField)
from wtforms.validators import (DataRequired, EqualTo, Email, Length,
                                NumberRange, Optional, ValidationError)
from app.models import User
from datetime import date
import re

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, message='A senha deve ter pelo menos 8 caracteres.')])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='As senhas devem ser iguais.')])
    submit = SubmitField('Cadastrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Este usuário já está em uso. Por favor, escolha outro.')

    def validate_password(self, password):
        if not re.search(r'[\d\W]', password.data):
            raise ValidationError('A senha deve conter pelo menos um número ou caractere especial.')

class ContactForm(FlaskForm):
    contact_type = SelectField('Tipo', choices=[
        ('Pessoa', 'Pessoa'),
        ('Empresa', 'Empresa'),
    ], default='Pessoa')
    customer_name = StringField('Nome / Razão Social', validators=[DataRequired()])
    email = StringField('E-mail', validators=[Optional(), Email(message='Formato de e-mail inválido.')])
    phone = StringField('Telefone', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Aberto', 'Aberto'),
        ('Aguardando Cliente', 'Aguardando Cliente'),
        ('Resolvido', 'Resolvido'),
        ('Cancelado', 'Cancelado'),
    ], validators=[DataRequired()])
    deadline = DateField('Prazo', format='%Y-%m-%d', validators=[])
    observations = TextAreaField('Observações')
    submit = SubmitField('Salvar')

    def validate_deadline(self, deadline):
        if deadline.data and deadline.data < date.today():
            raise ValidationError('A Data Limite de Retorno não pode ser no passado.')

class ImportForm(FlaskForm):
    csv_file = FileField('Arquivo CSV', validators=[
        FileRequired(message='É necessário selecionar um arquivo.'),
        FileAllowed(['csv'], 'Apenas arquivos .csv são permitidos.')
    ])
    submit = SubmitField('Importar Dados')


class LogoutForm(FlaskForm):
    submit = SubmitField('Sair')


class DeleteContactForm(FlaskForm):
    submit = SubmitField('Excluir')


class SystemSettingsForm(FlaskForm):
    days_inactive_alert = IntegerField('Dias para alerta',
                                       validators=[DataRequired(), NumberRange(min=1, max=365)])
    submit = SubmitField('Salvar Configurações')
