"""Use case for importing contacts from CSV — testable without any framework."""

from __future__ import annotations

import csv
import io
from typing import Sequence

from app.domain.entities.contact import Contact, ALLOWED_STATUSES


def sanitize_text(text: str | None) -> str:
    """Basic text cleanup — the infra layer can add HTML sanitization."""
    if not text:
        return ""
    return text.strip()


def parse_contact_row(row: Sequence[str]) -> Contact:
    """Parse a single CSV row into a domain Contact.

    Raises ValueError for invalid data.
    """
    if not row or not row[0].strip():
        raise ValueError("Nome do cliente é obrigatório.")

    customer_name = sanitize_text(row[0])
    status_raw = sanitize_text(row[1]) if len(row) > 1 and row[1].strip() else "Aberto"
    status = status_raw.title()
    if status not in ALLOWED_STATUSES:
        status = "Aberto"

    deadline = None
    if len(row) > 2 and row[2].strip():
        from datetime import datetime

        try:
            deadline = datetime.strptime(row[2].strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(
                f"Data inválida: '{row[2].strip()}'. Use YYYY-MM-DD."
            )

    observations = sanitize_text(row[3]) if len(row) > 3 else ""

    return Contact(
        customer_name=customer_name,
        status=status,
        deadline=deadline,
        observations=observations,
    )


def parse_csv_content(content: str) -> tuple[list[Contact], list[str]]:
    """Parse full CSV content into a list of domain Contacts.

    Returns (contacts, errors).
    """
    stream = io.StringIO(content, newline=None)
    reader = csv.reader(stream)
    next(reader, None)  # skip header

    contacts: list[Contact] = []
    errors: list[str] = []

    for idx, row in enumerate(reader, start=2):
        if not row or not row[0].strip():
            continue
        try:
            contact = parse_contact_row(row)
            contacts.append(contact)
        except ValueError as exc:
            errors.append(f"Linha {idx}: {exc}")

    return contacts, errors
