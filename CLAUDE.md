# MiniCRM — Referência do Projeto

## Stack
- **Back-end:** Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF
- **Front-end:** Tailwind CSS (CDN), JetBrains Mono, Material Symbols Outlined, ApexCharts (CDN)
- **DB:** SQLite (dev) via SQLAlchemy
- **Testes:** pytest (9 testes de segurança)

## Status de Atendimento (ENUM manual)
Os status válidos são definidos em `app/forms.py` → `ContactForm.status.choices` e validados em `app/views.py` → `import_csv`.

**Status atuais:**
- `Aberto`
- `Aguardando Cliente`
- `Resolvido`
- `Cancelado` ← adicionado na sessão de 2026-03-03

**Para adicionar um novo status, editar TODOS estes pontos:**
1. `app/forms.py` → `ContactForm.status.choices` (lista de tuplas)
2. `app/views.py` → `import_csv` → lista `status_capitalized not in [...]`
3. `app/views.py` → `dashboard()` → queries de contagem por status
4. `app/templates/index.html` → bloco de `<option>` no filtro de status + badges da tabela
5. `app/templates/dashboard.html` → séries dos gráficos ApexCharts

## Modelos de Dados (`app/models.py`)

### User
| Campo | Tipo | Notas |
|---|---|---|
| `id` | Integer PK | |
| `username` | String(64) | único |
| `password_hash` | String(256) | |
| `role` | String(20) | `'Operador'` ou `'Gestor'` |

### Contact
| Campo | Tipo | Notas |
|---|---|---|
| `id` | Integer PK | |
| `customer_name` | String(150) | |
| `status` | String(30) | enum manual (ver acima) |
| `deadline` | Date | nullable |
| `observations` | Text | sanitizado (XSS) |
| `created_at` | DateTime | default = utcnow |
| `user_id` | FK → User.id | dono do contato |
| `owner` | relationship | backref `contacts` |

## Rotas (`app/views.py`)

| Método | URL | Função | Acesso |
|---|---|---|---|
| GET/POST | `/` ou `/index` | `index()` | login |
| GET | `/dashboard` | `dashboard()` | Gestor |
| GET/POST | `/contact/new` | `new_contact()` | login |
| GET/POST | `/contact/<id>/edit` | `edit_contact()` | login + IDOR |
| POST | `/contact/<id>/delete` | `delete_contact()` | login + IDOR |
| GET/POST | `/import` | `import_csv()` | login |
| GET/POST | `/login` | `login()` | anon |
| GET/POST | `/register` | `register()` | anon |
| GET | `/logout` | `logout()` | login |

## Templates (`app/templates/`)

| Arquivo | Herda | Descrição |
|---|---|---|
| `base.html` | — | Layout global: navbar, flash msgs, footer, Dark/Light toggle |
| `index.html` | base | Dashboard: cards, tabela paginada, activity log |
| `dashboard.html` | base | Métricas (Gestor): cards + gráficos ApexCharts |
| `form.html` | base | Novo/Editar contato |
| `import.html` | base | Importar CSV |
| `login.html` | base | Auth login |
| `register.html` | base | Registro de usuário |

## Variáveis passadas ao `dashboard.html`
- `metrics` → dict: `{total, abertos, aguardando, resolvidos, cancelados, overdue}`
- `monthly_labels` → list[str]: `['Jan/25', ..., 'Mar/26']` (6 meses)
- `monthly_values` → list[int]: contagens correspondentes
- `donut_data` → list[int]: `[abertos, aguardando, resolvidos, cancelados]`
- `operator_names` → list[str]: usernames dos operadores
- `operator_series` → list[dict]: uma série por status `{name, data: [...]}`

## CSS e Design
- **Paleta:** CSS Variables via `:root` (light) e `.dark` (dark)
  - `--bg`, `--fg`, `--border`, `--muted`, `--surface`
- **Font:** JetBrains Mono em tudo (via Google Fonts CDN)
- **Clip:** classe `.clip` = chamfered corners (polygon clip-path)
- **Dark Mode:** toggle no header salva em `localStorage.theme`
- **Transições:** `* { transition: background-color 0.2s, border-color 0.2s, color 0.15s }`

## Gráficos (ApexCharts via CDN)
Carregados no `dashboard.html`. O tema é detectado no load:
```js
const isDark = document.documentElement.classList.contains('dark');
```
**Gráficos presentes:**
1. `chart-donut` — Distribuição por status (Donut)
2. `chart-bar` — Volume por mês (Barras)

**Gráficos planejados:**
3. `chart-line` — Abertos vs Resolvidos por mês (Linha dupla)
4. `chart-stacked` — Status por operador (Barras empilhadas)
5. `chart-gauge` — Taxa de SLA (Gauge/Radial)

## Segurança
- IDOR: `_get_contact_or_404()` — operadores só acessam seus próprios contatos
- XSS: `sanitize_html()` — remove tags HTML das observações
- CSRF: Flask-WTF em todos os forms (`{{ form.hidden_tag() }}`)
- Session: `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE = 'Lax'`
- Senha: mínimo 8 chars + número ou especial

## Executar a Aplicação
```bash
# Ativar venv
venv\Scripts\activate   # Windows

# Rodar
python run.py

# Testes
python -m pytest tests/ -v
```

## Variáveis de Ambiente (`.env`)
```
SECRET_KEY=sua_chave_secreta_aqui
DATABASE_URL=sqlite:///minicrm.db  # opcional
```
