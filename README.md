# Mini CRM Simples

Este é um Mini CRM simples(MVP) desenvolvido em Python e Flask com banco de dados SQLite para controle de contatos e pendências.

## Funcionalidades
- Cadastro de cliente e registro de contato.
- Status do atendimento (Aberto, Aguardando Cliente, Resolvido).
- Campo para data limite de retorno.
- Destaque visual laranja/amarelo em atendimentos com prazo vencido.
- Filtros por Status, Ordenação por Data de Vencimento e Recentes.
- Sistema de login básico (admin padrão).
- Layout responsivo simples via HTML/CSS (flexbox/grid).

## Como Instalar e Rodar Localmente (Windows)

1. **Abra o terminal** na pasta do projeto (`d:\Desenvolvimento\minicrm`).
2. **Ative o ambiente virtual** (se já não estiver ativo):
   ```powershell
   .\venv\Scripts\activate
   ```
3. (Opcional) **Instale as dependências** (já instaladas):
   ```powershell
   pip install -r requirements.txt
   ```
4. (Opcional) **Inicialize o Banco de Dados** (já inicializado no setup):
   ```powershell
   python init_db.py
   ```
   *Isso criará o arquivo `app.db` na raiz e o usuário padrão.*
   
5. **Inicie o Servidor Local**:
   ```powershell
   python run.py
   ```
6. **Acesse no navegador**:
   [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Acesso Padrão
- **Usuário**: admin
- **Senha**: admin

## Tecnologias Utilizadas
- **Backend**: Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **Banco de Dados**: SQLite
- **Frontend**: HTML5, Jinja2, CSS3 (variáveis, flexbox), Google Fonts (Inter)
