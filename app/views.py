import json

from flask import (render_template, flash, redirect, url_for, request, Response,
                   abort, jsonify)
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, Contact, AuditLog, SystemSettings
from app.forms import (ContactForm, DeleteContactForm, ImportForm,
                       LoginForm, LogoutForm, RegistrationForm,
                       SystemSettingsForm)
from app.services.auth import clear_login_failures, is_login_blocked, register_login_failure
from app.services.system import get_setting
from app.services.utils import (format_datetime_brt, sanitize_for_spreadsheet,
                                sanitize_html)
from app.tasks import enqueue_import_job, get_job_status
from flask import current_app as app
from sqlalchemy import desc, asc, func
from datetime import date, datetime, timedelta, timezone
import csv
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

ALLOWED_STATUSES = {'Aberto', 'Aguardando Cliente', 'Resolvido', 'Cancelado'}
LOGIN_ATTEMPTS: dict[tuple[str, str], list[datetime]] = {}



def record_audit(action: str, target_type: str, target_id: int | None = None, details: str | None = None):
    """Registra uma ação no log de auditoria."""
    log = AuditLog(
        user_id=current_user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    db.session.add(log)



def _get_contact_or_404(contact_id):
    """Retorna o contato se o usuário tem permissão, senão 404.
    Operadores só veem seus próprios contatos (oculta a existência de recursos alheios).
    Gestores têm visibilidade global.
    """
    if current_user.role == 'Gestor':
        return db.get_or_404(Contact, contact_id)
    return Contact.query.filter_by(
        id=contact_id, user_id=current_user.id
    ).first_or_404()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    status_filter = request.args.get('status', 'Todos')
    sort_by = request.args.get('sort', 'deadline')
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Contact.query

    # Operators can only see their own contacts
    if current_user.role == 'Operador':
        query = query.filter_by(user_id=current_user.id)

    if status_filter != 'Todos':
        query = query.filter_by(status=status_filter)
        
    if search_query:
        query = query.filter(Contact.customer_name.ilike(f'%{search_query}%'))

    if sort_by == 'deadline_desc':
        query = query.order_by(Contact.deadline.desc())
    elif sort_by == 'deadline_asc':
        query = query.order_by(Contact.deadline.asc())
    elif sort_by == 'created_desc':
        query = query.order_by(Contact.created_at.desc())
    else:
        # Default sort
        query = query.order_by(Contact.deadline.asc())

    contacts = query.paginate(page=page, per_page=15, error_out=False)

    # Calculate metrics for the Dashboard cards
    base_query = Contact.query if current_user.role == 'Gestor' else Contact.query.filter_by(user_id=current_user.id)
    total_contacts = base_query.count()
    pendentes_now = base_query.filter(Contact.status != 'Resolvido').count()
    resolvidos_total = base_query.filter_by(status='Resolvido').count()
    overdue_count = base_query.filter(Contact.status != 'Resolvido', Contact.deadline < date.today()).count()

    # 5 most recent contacts for the Activity Log
    recent_contacts = base_query.order_by(Contact.created_at.desc()).limit(5).all()

    # Inactive contacts alert
    inactive_days = int(get_setting('days_inactive_alert', '8'))
    inactive_threshold = datetime.now(timezone.utc) - timedelta(days=inactive_days)
    inactive_count = base_query.filter(
        Contact.status.notin_(['Resolvido', 'Cancelado']),
        Contact.created_at <= inactive_threshold
    ).count()

    metrics = {
        'total': total_contacts,
        'pendentes': pendentes_now,
        'resolvidos': resolvidos_total,
        'overdue': overdue_count,
        'inactive': inactive_count,
        'inactive_days': inactive_days,
    }

    return render_template('index.html', title='MiniCRM', contacts=contacts, status_filter=status_filter, sort_by=sort_by, search_query=search_query, metrics=metrics, recent_contacts=recent_contacts, inactive_days=inactive_days, delete_form=DeleteContactForm())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        blocked, retry_seconds = is_login_blocked(LOGIN_ATTEMPTS, form.username.data)
        if blocked:
            retry_minutes = max(1, retry_seconds // 60)
            flash(f'Muitas tentativas de login. Tente novamente em aproximadamente {retry_minutes} minuto(s).', 'error')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            register_login_failure(LOGIN_ATTEMPTS, form.username.data)
            app.logger.warning(f"Tentativa de login falha para o usuário: {form.username.data}")
            flash('Usuário ou senha inválidos.')
            return redirect(url_for('login'))
        clear_login_failures(LOGIN_ATTEMPTS, form.username.data)
        login_user(user, remember=form.remember_me.data)
        app.logger.info(f"Login bem-sucedido: {user.username}")
        return redirect(url_for('index'))
    return render_template('login.html', title='Entrar', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, role='Operador')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Agora você pode fazer login.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Cadastrar', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'Gestor':
        flash('Acesso negado. Apenas Gestores podem acessar o painel de métricas.')
        return redirect(url_for('index'))

    # ── Métricas Gerais ─────────────────────────────────────────────────────
    total = Contact.query.count()
    abertos     = Contact.query.filter_by(status='Aberto').count()
    aguardando  = Contact.query.filter_by(status='Aguardando Cliente').count()
    resolvidos  = Contact.query.filter_by(status='Resolvido').count()
    cancelados  = Contact.query.filter_by(status='Cancelado').count()
    overdue_count = Contact.query.filter(
        Contact.status.notin_(['Resolvido', 'Cancelado']),
        Contact.deadline < date.today()
    ).count()

    metrics = {
        'total': total,
        'abertos': abertos,
        'aguardando': aguardando,
        'resolvidos': resolvidos,
        'cancelados': cancelados,
        'overdue': overdue_count,
    }

    # ── Helpers de mês ──────────────────────────────────────────────────────
    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    today = date.today()

    def get_month_year(offset):
        """Retorna (month 1-12, year) para hoje menos `offset` meses."""
        m = today.month - offset
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        return m, y

    months = [get_month_year(i) for i in range(5, -1, -1)]   # mais antigo → mais recente
    monthly_labels = [f"{month_names[m-1]}/{str(y)[-2:]}" for m, y in months]

    def count_by_month_status(status_val):
        result = []
        for m, y in months:
            c = Contact.query.filter(
                Contact.status == status_val,
                db.extract('year',  Contact.created_at) == y,
                db.extract('month', Contact.created_at) == m,
            ).count()
            result.append(c)
        return result

    # Gráfico 1 – Donut (distribuição status)
    donut_data = [abertos, aguardando, resolvidos, cancelados]

    # Gráfico 2 – Barras (total por mês)
    monthly_values = []
    for m, y in months:
        c = Contact.query.filter(
            db.extract('year',  Contact.created_at) == y,
            db.extract('month', Contact.created_at) == m,
        ).count()
        monthly_values.append(c)

    # Gráfico 3 – Linha dupla (Abertos criados vs Resolvidos criados por mês)
    monthly_abertos   = count_by_month_status('Aberto')
    monthly_resolvidos = count_by_month_status('Resolvido')

    # Gráfico 4 – Barras empilhadas por operador
    operators = User.query.filter_by(role='Operador').all()
    operator_names = [u.username for u in operators]
    op_statuses = ['Aberto', 'Aguardando Cliente', 'Resolvido', 'Cancelado']
    op_colors   = ['#3b82f6', '#f97316', '#22c55e', '#9ca3af']
    operator_series = []
    for s in op_statuses:
        data = []
        for u in operators:
            c = Contact.query.filter_by(user_id=u.id, status=s).count()
            data.append(c)
        operator_series.append({'name': s, 'data': data})

    # Gráfico 5 – Gauge SLA
    active = Contact.query.filter(Contact.status.notin_(['Resolvido', 'Cancelado'])).count()
    sla_rate = round((1 - overdue_count / active) * 100, 1) if active > 0 else 100.0

    return render_template('dashboard.html', title='Métricas',
                           metrics=metrics,
                           monthly_labels=monthly_labels,
                           monthly_values=monthly_values,
                           donut_data=donut_data,
                           monthly_abertos=monthly_abertos,
                           monthly_resolvidos=monthly_resolvidos,
                           operator_names=operator_names,
                           operator_series=operator_series,
                           op_colors=op_colors,
                           sla_rate=sla_rate)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    form = LogoutForm()
    if not form.validate_on_submit():
        flash('Requisição inválida.', 'error')
        return redirect(url_for('index'))
    logout_user()
    return redirect(url_for('login'))

@app.route('/contact/new', methods=['GET', 'POST'])
@login_required
def new_contact():
    form = ContactForm()
    if form.validate_on_submit():
        contact = Contact(
            contact_type=form.contact_type.data,
            customer_name=form.customer_name.data,
            email=form.email.data or None,
            phone=form.phone.data or None,
            status=form.status.data,
            deadline=form.deadline.data,
            observations=sanitize_html(form.observations.data),
            owner=current_user
        )
        db.session.add(contact)
        db.session.flush()  # Get the contact.id before committing
        record_audit('criou', 'Contact', contact.id)
        db.session.commit()
        flash('Novo contato adicionado com sucesso!')
        return redirect(url_for('index'))
    return render_template('form.html', title='Novo Contato', form=form, legend='Novo Contato')

@app.route('/contact/<int:contact_id>/view')
@login_required
def view_contact(contact_id):
    """Exibe um contato em modo somente leitura."""
    contact = _get_contact_or_404(contact_id)
    return render_template('contact_view.html', title=f'Contato: {contact.customer_name}', contact=contact)

@app.route('/contact/<int:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    contact = _get_contact_or_404(contact_id)

    form = ContactForm()
    if form.validate_on_submit():
        old_status = contact.status
        contact.contact_type   = form.contact_type.data
        contact.customer_name  = form.customer_name.data
        contact.email          = form.email.data or None
        contact.phone          = form.phone.data or None
        contact.status         = form.status.data
        contact.deadline       = form.deadline.data
        contact.observations   = sanitize_html(form.observations.data)
        details = f'{old_status} → {contact.status}' if old_status != contact.status else None
        record_audit('editou', 'Contact', contact.id, details=details)
        db.session.commit()
        flash('O contato foi atualizado!')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.contact_type.data  = contact.contact_type or 'Pessoa'
        form.customer_name.data = contact.customer_name
        form.email.data         = contact.email
        form.phone.data         = contact.phone
        form.status.data        = contact.status
        form.deadline.data      = contact.deadline
        form.observations.data  = contact.observations

    return render_template('form.html', title='Editar Contato', form=form, legend='Editar Contato')

@app.route('/contact/<int:contact_id>/delete', methods=['POST'])
@login_required
def delete_contact(contact_id):
    form = DeleteContactForm()
    if not form.validate_on_submit():
        abort(400)
    contact = _get_contact_or_404(contact_id)
    contact_id_log = contact.id
    record_audit('excluiu', 'Contact', contact_id_log)
    db.session.delete(contact)
    db.session.commit()
    flash('O contato foi excluído.')
    return redirect(url_for('index'))


@app.route('/export/<fmt>')
@login_required
def export_contacts(fmt):
    """Exporta os contatos (respeitando filtro e papel do usuário) em CSV ou XLSX."""
    if fmt not in ('csv', 'xlsx'):
        flash('Formato de exportação inválido.')
        return redirect(url_for('index'))

    # ── Mesma query da rota index, sem paginação ─────────────────────────────
    status_filter = request.args.get('status', 'Todos')
    search_query  = request.args.get('search', '').strip()
    sort_by       = request.args.get('sort', 'deadline_asc')

    query = Contact.query
    if current_user.role == 'Operador':
        query = query.filter_by(user_id=current_user.id)
    if status_filter != 'Todos':
        query = query.filter_by(status=status_filter)
    if search_query:
        query = query.filter(Contact.customer_name.ilike(f'%{search_query}%'))
    if sort_by == 'deadline_desc':
        query = query.order_by(Contact.deadline.desc())
    elif sort_by == 'created_desc':
        query = query.order_by(Contact.created_at.desc())
    else:
        query = query.order_by(Contact.deadline.asc())

    contacts = query.all()

    # ── Cabeçalho das colunas ────────────────────────────────────────────────
    headers = ['ID', 'Tipo', 'Nome / Razão Social', 'E-mail', 'Telefone', 'Status', 'Responsável', 'Prazo', 'Observações', 'Criado em']

    def row_data(c):
        return [
            c.id,
            sanitize_for_spreadsheet(c.contact_type or 'Pessoa'),
            sanitize_for_spreadsheet(c.customer_name),
            sanitize_for_spreadsheet(c.email or ''),
            sanitize_for_spreadsheet(c.phone or ''),
            sanitize_for_spreadsheet(c.status),
            sanitize_for_spreadsheet(c.owner.username if c.owner else ''),
            sanitize_for_spreadsheet(c.deadline.strftime('%d/%m/%Y') if c.deadline else ''),
            sanitize_for_spreadsheet(c.observations or ''),
            sanitize_for_spreadsheet(format_datetime_brt(c.created_at, '%d/%m/%Y %H:%M')),
        ]

    timestamp = datetime.now().strftime('%Y%m%d_%H%M')

    # ── CSV ──────────────────────────────────────────────────────────────────
    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        for c in contacts:
            writer.writerow(row_data(c))
        output.seek(0)
        return Response(
            output.getvalue().encode('utf-8-sig'),   # BOM para Excel abrir corretamente
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=atendimentos_{timestamp}.csv'}
        )

    # ── XLSX ─────────────────────────────────────────────────────────────────
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Atendimentos'

    # Cabeçalho estilizado
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(fill_type='solid', fgColor='111111')
    header_align = Alignment(horizontal='center', vertical='center')

    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    # Dados
    for row_idx, c in enumerate(contacts, start=2):
        for col_idx, value in enumerate(row_data(c), start=1):
            ws.cell(row=row_idx, column=col_idx, value=value)

    # Largura automática das colunas
    for col in ws.columns:
        max_len = max((len(str(cell.value or '')) for cell in col), default=8)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename=atendimentos_{timestamp}.xlsx'}
    )


@app.route('/export_metrics/<fmt>')
@login_required
def export_metrics(fmt):
    """Exporta as métricas do dashboard em CSV ou XLSX (apenas Gestores)."""
    if current_user.role != 'Gestor':
        flash('Acesso negado.')
        return redirect(url_for('index'))
    if fmt not in ('csv', 'xlsx'):
        flash('Formato inválido.')
        return redirect(url_for('dashboard'))

    total = Contact.query.count()
    abertos    = Contact.query.filter_by(status='Aberto').count()
    aguardando = Contact.query.filter_by(status='Aguardando Cliente').count()
    resolvidos = Contact.query.filter_by(status='Resolvido').count()
    cancelados = Contact.query.filter_by(status='Cancelado').count()
    overdue    = Contact.query.filter(
        Contact.status.notin_(['Resolvido', 'Cancelado']),
        Contact.deadline < date.today()
    ).count()
    active = Contact.query.filter(Contact.status.notin_(['Resolvido', 'Cancelado'])).count()
    sla_rate = round((1 - overdue / active) * 100, 1) if active > 0 else 100.0

    operators = User.query.filter_by(role='Operador').all()
    op_rows = []
    for u in operators:
        op_rows.append([
            u.username,
            Contact.query.filter_by(user_id=u.id, status='Aberto').count(),
            Contact.query.filter_by(user_id=u.id, status='Aguardando Cliente').count(),
            Contact.query.filter_by(user_id=u.id, status='Resolvido').count(),
            Contact.query.filter_by(user_id=u.id, status='Cancelado').count(),
        ])

    timestamp = datetime.now().strftime('%Y%m%d_%H%M')

    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(['Resumo de Métricas', f'Exportado em {datetime.now().strftime("%d/%m/%Y %H:%M")}'])
        writer.writerow([])
        writer.writerow(['Métrica', 'Valor'])
        writer.writerow(['Total de Atendimentos', total])
        writer.writerow(['Abertos', abertos])
        writer.writerow(['Aguardando Cliente', aguardando])
        writer.writerow(['Resolvidos', resolvidos])
        writer.writerow(['Cancelados', cancelados])
        writer.writerow(['Atrasados', overdue])
        writer.writerow(['SLA (%)', sla_rate])
        writer.writerow([])
        writer.writerow(['Operador', 'Abertos', 'Aguardando', 'Resolvidos', 'Cancelados'])
        for row in op_rows:
            writer.writerow([sanitize_for_spreadsheet(row[0]), *row[1:]])
        output.seek(0)
        return Response(
            output.getvalue().encode('utf-8-sig'),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=metricas_{timestamp}.csv'}
        )

    # XLSX
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Métricas'
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(fill_type='solid', fgColor='111111')

    summary_data = [
        ('Métrica', 'Valor'),
        ('Total de Atendimentos', total),
        ('Abertos', abertos),
        ('Aguardando Cliente', aguardando),
        ('Resolvidos', resolvidos),
        ('Cancelados', cancelados),
        ('Atrasados', overdue),
        ('SLA (%)', sla_rate),
    ]
    for r_idx, (label, val) in enumerate(summary_data, start=1):
        c1 = ws.cell(row=r_idx, column=1, value=label)
        c2 = ws.cell(row=r_idx, column=2, value=val)
        if r_idx == 1:
            c1.font = header_font; c1.fill = header_fill
            c2.font = header_font; c2.fill = header_fill

    ws.cell(row=len(summary_data)+2, column=1, value='Por Operador')
    op_headers = ['Operador', 'Abertos', 'Aguardando', 'Resolvidos', 'Cancelados']
    for c_idx, h in enumerate(op_headers, 1):
        cell = ws.cell(row=len(summary_data)+3, column=c_idx, value=h)
        cell.font = header_font; cell.fill = header_fill
    for r_idx, row in enumerate(op_rows, start=len(summary_data)+4):
        for c_idx, val in enumerate(row, 1):
            ws.cell(row=r_idx, column=c_idx, value=val)

    for col in ws.columns:
        max_len = max((len(str(cell.value or '')) for cell in col), default=8)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename=metricas_{timestamp}.xlsx'}
    )



@app.route('/export_metrics/pdf')
@login_required
def export_metrics_pdf():
    """Exporta as métricas do dashboard em PDF (apenas Gestores)."""
    if current_user.role != 'Gestor':
        flash('Acesso negado.')
        return redirect(url_for('index'))

    from fpdf import FPDF
    from datetime import timezone, timedelta

    # ── Coleta de dados ───────────────────────────────────────────────────────
    total     = Contact.query.count()
    abertos   = Contact.query.filter_by(status='Aberto').count()
    aguardando = Contact.query.filter_by(status='Aguardando Cliente').count()
    resolvidos = Contact.query.filter_by(status='Resolvido').count()
    cancelados = Contact.query.filter_by(status='Cancelado').count()
    overdue   = Contact.query.filter(
        Contact.status.notin_(['Resolvido', 'Cancelado']),
        Contact.deadline < date.today()
    ).count()
    active    = Contact.query.filter(Contact.status.notin_(['Resolvido', 'Cancelado'])).count()
    sla_rate  = round((1 - overdue / active) * 100, 1) if active > 0 else 100.0

    operators = User.query.filter_by(role='Operador').all()
    op_rows   = []
    for u in operators:
        op_rows.append([
            u.username,
            Contact.query.filter_by(user_id=u.id, status='Aberto').count(),
            Contact.query.filter_by(user_id=u.id, status='Aguardando Cliente').count(),
            Contact.query.filter_by(user_id=u.id, status='Resolvido').count(),
            Contact.query.filter_by(user_id=u.id, status='Cancelado').count(),
        ])

    BRT = timezone(timedelta(hours=-3))
    now_brt = datetime.now(timezone.utc).astimezone(BRT).strftime('%d/%m/%Y %H:%M')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')

    # ── Helpers UTF-8 → latin-1 safe ─────────────────────────────────────────
    _PDF_CHARS = {
        '\u2014': '-', '\u2013': '-',
        '\u2019': "'", '\u2018': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2026': '...', '\xa0': ' ',
    }

    def pdf_safe(text):
        s = str(text)
        for ch, rep in _PDF_CHARS.items():
            s = s.replace(ch, rep)
        return s.encode('latin-1', errors='replace').decode('latin-1')

    # ── PDF ──────────────────────────────────────────────────────────────────
    class PDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 11)
            self.set_fill_color(17, 17, 17)
            self.set_text_color(240, 240, 240)
            self.cell(0, 10, 'MiniCRM - Relatorio de Metricas', align='L', fill=True, new_x='LMARGIN', new_y='NEXT')
            self.set_font('Helvetica', '', 8)
            self.set_text_color(136, 136, 136)
            self.cell(0, 6, pdf_safe(f'Gerado em {now_brt}'), new_x='LMARGIN', new_y='NEXT')
            self.ln(3)

        def footer(self):
            self.set_y(-12)
            self.set_font('Helvetica', '', 8)
            self.set_text_color(136, 136, 136)
            self.cell(0, 8, pdf_safe(f'Pagina {self.page_no()}'), align='C')

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Seção: Resumo
    def section_title(text):
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(17, 17, 17)
        pdf.cell(0, 7, pdf_safe(text), fill=True, new_x='LMARGIN', new_y='NEXT')
        pdf.ln(1)

    def metric_row(label, value, highlight=False):
        pdf.set_font('Helvetica', '', 9)
        if highlight:
            pdf.set_text_color(239, 68, 68)
        else:
            pdf.set_text_color(17, 17, 17)
        pdf.cell(100, 6, pdf_safe(label))
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 6, pdf_safe(value), new_x='LMARGIN', new_y='NEXT')
        pdf.set_text_color(17, 17, 17)

    section_title('Visao Geral')
    metric_row('Total de Atendimentos', total)
    metric_row('Abertos', abertos)
    metric_row('Aguardando Cliente', aguardando)
    metric_row('Resolvidos', resolvidos)
    metric_row('Cancelados', cancelados)
    metric_row('Atrasados (prazo expirado)', overdue, highlight=overdue > 0)
    metric_row('Taxa de SLA (%)', f'{sla_rate}%', highlight=sla_rate < 70)
    pdf.ln(4)

    # Seção: Por Operador
    if op_rows:
        section_title('Desempenho por Operador')
        col_labels = ['Operador', 'Abertos', 'Aguardando', 'Resolvidos', 'Cancelados']
        col_widths  = [60, 28, 28, 28, 28]
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(17, 17, 17)
        pdf.set_text_color(240, 240, 240)
        for label, w in zip(col_labels, col_widths):
            pdf.cell(w, 6, pdf_safe(label), fill=True, border=0)
        pdf.ln()
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(17, 17, 17)
        for i, row in enumerate(op_rows):
            if i % 2 == 0:
                pdf.set_fill_color(250, 250, 250)
            else:
                pdf.set_fill_color(255, 255, 255)
            for val, w in zip(row, col_widths):
                pdf.cell(w, 6, pdf_safe(val), fill=True, border=0)
            pdf.ln()

    output = io.BytesIO(pdf.output())
    return Response(
        output.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=metricas_{timestamp}.pdf'}
    )


@app.route('/export_bi')
@login_required
def export_bi():
    """Exporta todos os contatos em CSV plano para Power BI / Looker Studio (apenas Gestores)."""
    if current_user.role != 'Gestor':
        flash('Acesso negado.')
        return redirect(url_for('index'))

    contacts = Contact.query.order_by(Contact.created_at.desc()).all()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    # Cabeçalho flat sem acentos (compatibilidade máxima com BI)
    writer.writerow([
        'id', 'tipo', 'nome', 'email', 'telefone',
        'status', 'responsavel', 'prazo', 'observacoes',
        'criado_em', 'atrasado'
    ])
    for c in contacts:
        writer.writerow([
            c.id,
            sanitize_for_spreadsheet(c.contact_type or 'Pessoa'),
            sanitize_for_spreadsheet(c.customer_name),
            sanitize_for_spreadsheet(c.email or ''),
            sanitize_for_spreadsheet(c.phone or ''),
            sanitize_for_spreadsheet(c.status),
            sanitize_for_spreadsheet(c.owner.username if c.owner else ''),
            sanitize_for_spreadsheet(c.deadline.strftime('%Y-%m-%d') if c.deadline else ''),
            sanitize_for_spreadsheet(c.observations or ''),
            sanitize_for_spreadsheet(format_datetime_brt(c.created_at, '%Y-%m-%d %H:%M:%S')),
            '1' if c.is_overdue() else '0',
        ])
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=minicrm_bi_{timestamp}.csv'}
    )


@app.route('/audit_logs')
@login_required
def audit_logs():
    """Página de logs de auditoria (apenas Gestores)."""
    if current_user.role != 'Gestor':
        flash('Acesso negado. Apenas Gestores podem visualizar os logs de auditoria.')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=30, error_out=False)
    return render_template('audit_logs.html', title='Log de Auditoria', logs=logs)


@app.route('/webhooks/notify', methods=['POST'])
def webhook_notify():
    token = request.headers.get('X-Webhook-Token', '')
    if token != app.config['WEBHOOK_TOKEN']:
        abort(403)
    payload = request.get_json(silent=True) or {}
    details = json.dumps(payload, default=str)
    record_audit('webhook', 'Webhook', None, details=details)
    app.logger.info(f"Webhook recebido (%s)", payload)
    return jsonify({'status': 'accepted'}), 202


@app.route('/alerts')
@login_required
def alert_history():
    if current_user.role != 'Gestor':
        flash('Acesso negado. Apenas Gestores podem ver alertas de integração.', 'error')
        return redirect(url_for('index'))
    alerts = AuditLog.query.filter_by(action='webhook').order_by(AuditLog.timestamp.desc()).limit(50).all()
    return render_template('alerts.html', alerts=alerts)


@app.route('/system_settings', methods=['GET', 'POST'])
@login_required
def system_settings():
    """Configurações do sistema (apenas Gestores)."""
    if current_user.role != 'Gestor':
        flash('Acesso negado. Apenas Gestores podem acessar as configurações.')
        return redirect(url_for('index'))

    form = SystemSettingsForm()
    days_inactive = get_setting('days_inactive_alert', '8')
    if request.method == 'GET':
        try:
            form.days_inactive_alert.data = int(days_inactive)
        except ValueError:
            form.days_inactive_alert.data = 8

    if form.validate_on_submit():
        days_value = str(form.days_inactive_alert.data)
        setting = SystemSettings.query.filter_by(key='days_inactive_alert').first()
        if setting:
            setting.value = days_value
        else:
            setting = SystemSettings(
                key='days_inactive_alert',
                value=days_value,
                description='Número de dias sem atividade para gerar alerta de inatividade'
            )
            db.session.add(setting)
        record_audit('alterou configuração', 'SystemSettings', None)
        db.session.commit()
        flash('Configurações salvas com sucesso!')
        return redirect(url_for('system_settings'))

    return render_template('system_settings.html', title='Configurações', days_inactive=days_inactive, form=form)


@app.route('/import', methods=['GET', 'POST'])
@login_required
def import_csv():
    form = ImportForm()
    if form.validate_on_submit():
        file = form.csv_file.data
        content = file.stream.read().decode("UTF8")
        job_id = enqueue_import_job(content, current_user.id)
        flash(f'Importação agendada (job {job_id}).', 'info')
        return redirect(url_for('import_status', job_id=job_id))
    return render_template('import.html', title='Importar Clientes', form=form)


@app.route('/import/status/<job_id>')
@login_required
def import_status(job_id):
    status = get_job_status(job_id, current_user.id)
    if status is None:
        abort(404)
    return render_template('import_status.html', job_id=job_id, status=status)
