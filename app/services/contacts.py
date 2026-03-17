from datetime import date

from app.models import Contact


ALLOWED_STATUSES = {'Resolvido', 'Cancelado'}


def base_query(user):
    query = Contact.query
    if user.role == 'Operador':
        query = query.filter_by(user_id=user.id)
    return query


def dashboard_metrics(user):
    query = base_query(user)
    total = query.count()
    pendentes = query.filter(Contact.status != 'Resolvido').count()
    resolvidos = query.filter_by(status='Resolvido').count()
    cancelados = query.filter_by(status='Cancelado').count()
    aguardando = query.filter_by(status='Aguardando Cliente').count()
    overdue = query.filter(
        Contact.status.notin_(['Resolvido', 'Cancelado']),
        Contact.deadline < date.today()
    ).count()
    return {
        'total': total,
        'pendentes': pendentes,
        'resolvidos': resolvidos,
        'cancelados': cancelados,
        'aguardando': aguardando,
        'overdue': overdue,
    }


def recent_contacts(user, limit=5):
    return base_query(user).order_by(Contact.created_at.desc()).limit(limit).all()
