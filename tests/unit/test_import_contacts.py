"""Unit tests for CSV import use case — no Flask, no DB."""

import pytest

from app.domain.use_cases.import_contacts import (
    parse_contact_row,
    parse_csv_content,
)


class TestParseContactRow:
    def test_basic_row(self):
        c = parse_contact_row(["Empresa X", "Aberto", "2026-06-15", "Nota"])
        assert c.customer_name == "Empresa X"
        assert c.status == "Aberto"
        assert c.deadline is not None
        assert c.observations == "Nota"

    def test_empty_status_defaults_to_aberto(self):
        c = parse_contact_row(["Empresa X", ""])
        assert c.status == "Aberto"

    def test_invalid_status_defaults_to_aberto(self):
        c = parse_contact_row(["Empresa X", "Inexistente"])
        assert c.status == "Aberto"

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError, match="Data inválida"):
            parse_contact_row(["Empresa X", "Aberto", "not-a-date"])

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="obrigatório"):
            parse_contact_row(["", "Aberto"])


class TestParseCsvContent:
    def test_parses_valid_csv(self):
        csv = "nome,status,deadline,obs\nEmpresa A,Aberto,2026-01-01,ok\nEmpresa B,,,"
        contacts, errors = parse_csv_content(csv)
        assert len(contacts) == 2
        assert len(errors) == 0

    def test_reports_errors_without_stopping(self):
        csv = "nome,status,deadline\nOK,Aberto,2026-01-01\nBad,Aberto,invalid-date\nAlsoOK,,"
        contacts, errors = parse_csv_content(csv)
        assert len(contacts) == 2
        assert len(errors) == 1
        assert "Linha 3" in errors[0]

    def test_skips_empty_rows(self):
        csv = "nome\n\n\nEmpresa\n"
        contacts, errors = parse_csv_content(csv)
        assert len(contacts) == 1
