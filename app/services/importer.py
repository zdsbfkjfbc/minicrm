import csv
import io
from typing import Sequence

from app import db
from app.models import Contact
from app.services.utils import sanitize_html

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
    stream = io.StringIO(content, newline=None)
    reader = csv.reader(stream)
    next(reader, None)
    contacts = []
    errors = []
    for idx, row in enumerate(reader, start=2):
        if not row or not row[0].strip():
            continue
        try:
            customer_name, status, deadline, observations = parse_contact_row(row)
        except ValueError as exc:
            errors.append(f"Linha {idx}: {exc}")
            continue

        contact = Contact(
            customer_name=customer_name,
            status=status,
            deadline=deadline,
            observations=observations,
            user_id=owner_id,
        )
        contacts.append(contact)
    return contacts, errors
