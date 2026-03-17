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

## Automatização de commits
Disponibilizamos `scripts/commit.ps1` para automatizar o fluxo estilo Big Tech (teste → staging → commit conforme convencional). Use assim:

```powershell
.\scripts\commit.ps1 -Type <feat|fix|docs|chore|refactor|test|ci|perf> -Scope <modulo?> -Summary "Breve descrição"
```

O script:

1. Executa `python -m pytest -q tests` (usa `SECRET_KEY='test-secret'` no ambiente).
2. Estagia tudo (`git add -A`).
3. Cria o commit com mensagem no formato `tipo(escopo): resumo`.

Se os testes falharem, o processo é abortado e o repositório permanece no estado anterior; assim você segura a qualidade antes de push.

## API v1
O projeto expõe um Blueprint `api_v1` que responde em `/api/v1/*`:

- `GET /api/v1/contacts`: lista até 25 contatos mais recentes do usuário autenticado em JSON (id, cliente, status, responsável, prazo e criado_em).
- `GET /api/v1/metrics`: retorna métricas agregadas (total, pendentes, resolvidos, cancelados, aguardando e atrasados) respeitando o papel do usuário.

Ambos os endpoints dependem da sessão Flask-Login e servem como base para uma interface API/serviço no futuro.

## Jobs e observabilidade
- Rotas como `/import` agora agendam jobs em background usando um executor (`app/tasks.py`); o status pode ser consultado em `/import/status/<job_id>`.
- Há um health check leve em `/healthz` que retorna `{"status":"ok","trace_id":...}`.
- O logger do Flask foi ajustado para usar formato JSON estruturado com `trace_id` (`X-Request-ID` é propagado nas respostas), facilitando conexão com observabilidade (Stackdriver, Honeycomb, Grafana Loki etc.).

## Infraestrutura e pipeline

- **Docker Compose:** suba `db`, `redis` e app com `docker-compose up --build`. O arquivo `docker-compose.yml` usa Postgres 16 e Redis 8, linkando `DATABASE_URL` e `REDIS_URL` via variáveis de ambiente documentadas em `.env.example`.
- **Makefile:** `make init` prepara o ambiente (instala dependências e registra hooks). Use `make lint`, `make test` e `make docker-up` para tarefas repetitivas.
- **Pre-commit & qualidade:** instalamos `black`, `ruff` e `pre-commit`. Rode `pre-commit run --all-files` localmente ou deixe o hook automático cuidar antes do commit.
- **CI GitHub Actions:** toda PR dispara o workflow `.github/workflows/ci.yml` que instala dependências, roda `black --check`, `ruff check` e a suíte `pytest` com `SECRET_KEY=test-secret`. Essa ação garante que o padrão "Big Tech" de qualidade não quebre.
