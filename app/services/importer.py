import csv
import io
from typing import Sequence

from app.models import Contact
from app.services.utils import sanitize_html
from app.domain.use_cases.import_contacts import parse_csv_content as parse_domain_csv

ALLOWED_STATUSES = {'Aberto', 'Aguardando Cliente', 'Resolvido', 'Cancelado'}


def parse_contact_row(row: Sequence[str]):
    customer_name = sanitize_html(row[0].strip())
    status = sanitize_html(row[1].strip()) if len(row) > 1 and row[1].strip() else 'Aberto'
    status_normalized = status.title()
    if status_normalized not in ALLOWED_STATUSES:
        status_normalized = 'Aberto'
    deadline = None
    if len(row) > 2 and row[2].strip():
        from datetime import datetime

        try:
            deadline = datetime.strptime(row[2].strip(), '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f"Data inválida: '{row[2].strip()}'. Use YYYY-MM-DD.")
    observations = sanitize_html(row[3].strip()) if len(row) > 3 else ''
    return customer_name, status_normalized, deadline, observations


def build_contacts(content: str, owner_id: int):
    domain_contacts, errors = parse_domain_csv(content)
    contacts = []
    for item in domain_contacts:
        contacts.append(
            Contact(
                customer_name=sanitize_html(item.customer_name),
                contact_type=item.contact_type,
                status=item.status,
                deadline=item.deadline,
                observations=sanitize_html(item.observations or ""),
                user_id=owner_id,
            )
        )
    return contacts, errors
