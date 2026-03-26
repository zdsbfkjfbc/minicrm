from flask import jsonify
from flask_login import current_user, login_required

from app.api.v1 import bp
from app.infra.repositories.sqlalchemy_contact_repo import (
    SqlAlchemyContactRepository,
)
from app.services.contacts import dashboard_metrics
from app.services.utils import format_datetime_brt


@bp.route('/contacts', methods=['GET'])
@login_required
def list_contacts():
    contacts = SqlAlchemyContactRepository().recent(
        user_id=current_user.id,
        is_gestor=(current_user.role == 'Gestor'),
        limit=25,
    )
    payload = [{
        'id': c.id,
        'cliente': c.customer_name,
        'status': c.status,
        'responsavel': c.owner_username,
        'prazo': format_datetime_brt(c.deadline, '%d/%m/%Y') if c.deadline else None,
        'criado_em': format_datetime_brt(c.created_at),
    } for c in contacts]
    return jsonify(payload)


@bp.route('/metrics', methods=['GET'])
@login_required
def metrics():
    return jsonify(dashboard_metrics(current_user))
