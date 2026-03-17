from flask import jsonify
from flask_login import current_user, login_required

from app.api.v1 import bp
from app.models import Contact
from app.services.contacts import base_query, dashboard_metrics
from app.services.utils import format_datetime_brt


@bp.route('/contacts', methods=['GET'])
@login_required
def list_contacts():
    query = base_query(current_user).order_by(Contact.created_at.desc()).limit(25)
    payload = [{
        'id': c.id,
        'cliente': c.customer_name,
        'status': c.status,
        'responsavel': c.owner.username if c.owner else None,
        'prazo': format_datetime_brt(c.deadline, '%d/%m/%Y') if c.deadline else None,
        'criado_em': format_datetime_brt(c.created_at),
    } for c in query]
    return jsonify(payload)


@bp.route('/metrics', methods=['GET'])
@login_required
def metrics():
    return jsonify(dashboard_metrics(current_user))
