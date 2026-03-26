"""CSV export functions for contacts and metrics."""

from __future__ import annotations

import csv
import io
from datetime import datetime

from app.domain.entities.contact import Contact
from app.services.utils import format_datetime_brt, sanitize_for_spreadsheet


def _contact_row(c: Contact) -> list:
    return [
        c.id,
        sanitize_for_spreadsheet(c.contact_type or "Pessoa"),
        sanitize_for_spreadsheet(c.customer_name),
        sanitize_for_spreadsheet(c.email or ""),
        sanitize_for_spreadsheet(c.phone or ""),
        sanitize_for_spreadsheet(c.status),
        sanitize_for_spreadsheet(c.owner_username or ""),
        sanitize_for_spreadsheet(
            c.deadline.strftime("%d/%m/%Y") if c.deadline else ""
        ),
        sanitize_for_spreadsheet(c.observations or ""),
        sanitize_for_spreadsheet(
            format_datetime_brt(c.created_at, "%d/%m/%Y %H:%M")
        ),
    ]


CONTACT_HEADERS = [
    "ID", "Tipo", "Nome / Razão Social", "E-mail", "Telefone",
    "Status", "Responsável", "Prazo", "Observações", "Criado em",
]


def export_contacts_csv(contacts: list[Contact]) -> bytes:
    """Return UTF-8-BOM-encoded CSV bytes for a list of contacts."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow(CONTACT_HEADERS)
    for c in contacts:
        writer.writerow(_contact_row(c))
    output.seek(0)
    return output.getvalue().encode("utf-8-sig")


def export_metrics_csv(data: dict) -> bytes:
    """Return UTF-8-BOM-encoded CSV bytes for metrics export."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow([
        "Resumo de Métricas",
        f'Exportado em {datetime.now().strftime("%d/%m/%Y %H:%M")}',
    ])
    writer.writerow([])
    writer.writerow(["Métrica", "Valor"])
    for label, key in [
        ("Total de Atendimentos", "total"),
        ("Abertos", "abertos"),
        ("Aguardando Cliente", "aguardando"),
        ("Resolvidos", "resolvidos"),
        ("Cancelados", "cancelados"),
        ("Atrasados", "overdue"),
        ("SLA (%)", "sla_rate"),
    ]:
        writer.writerow([label, data[key]])
    writer.writerow([])
    writer.writerow([
        "Operador", "Abertos", "Aguardando", "Resolvidos", "Cancelados"
    ])
    for row in data["op_rows"]:
        writer.writerow([sanitize_for_spreadsheet(row[0]), *row[1:]])
    output.seek(0)
    return output.getvalue().encode("utf-8-sig")


def export_bi_csv(contacts: list[Contact]) -> bytes:
    """Return UTF-8-BOM-encoded CSV bytes for BI export (flat, no accents)."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow([
        "id", "tipo", "nome", "email", "telefone",
        "status", "responsavel", "prazo", "observacoes",
        "criado_em", "atrasado",
    ])
    for c in contacts:
        writer.writerow([
            c.id,
            sanitize_for_spreadsheet(c.contact_type or "Pessoa"),
            sanitize_for_spreadsheet(c.customer_name),
            sanitize_for_spreadsheet(c.email or ""),
            sanitize_for_spreadsheet(c.phone or ""),
            sanitize_for_spreadsheet(c.status),
            sanitize_for_spreadsheet(c.owner_username or ""),
            sanitize_for_spreadsheet(
                c.deadline.strftime("%Y-%m-%d") if c.deadline else ""
            ),
            sanitize_for_spreadsheet(c.observations or ""),
            sanitize_for_spreadsheet(
                format_datetime_brt(c.created_at, "%Y-%m-%d %H:%M:%S")
            ),
            "1" if c.is_overdue() else "0",
        ])
    output.seek(0)
    return output.getvalue().encode("utf-8-sig")
