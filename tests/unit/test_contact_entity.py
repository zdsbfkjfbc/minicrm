"""Unit tests for the Contact domain entity — no Flask, no DB."""

import pytest
from datetime import date, timedelta

from app.domain.entities.contact import Contact


class TestContactIsOverdue:
    def test_overdue_when_past_deadline_and_not_resolved(self):
        c = Contact(
            customer_name="Test",
            status="Aberto",
            deadline=date.today() - timedelta(days=1),
        )
        assert c.is_overdue() is True

    def test_not_overdue_when_resolved(self):
        c = Contact(
            customer_name="Test",
            status="Resolvido",
            deadline=date.today() - timedelta(days=1),
        )
        assert c.is_overdue() is False

    def test_not_overdue_when_no_deadline(self):
        c = Contact(customer_name="Test", status="Aberto", deadline=None)
        assert c.is_overdue() is False

    def test_not_overdue_when_deadline_is_today(self):
        c = Contact(
            customer_name="Test",
            status="Aberto",
            deadline=date.today(),
        )
        assert c.is_overdue() is False

    def test_not_overdue_when_deadline_is_future(self):
        c = Contact(
            customer_name="Test",
            status="Aberto",
            deadline=date.today() + timedelta(days=5),
        )
        assert c.is_overdue() is False


class TestContactValidation:
    def test_valid_status_passes(self):
        c = Contact(customer_name="Test", status="Aberto")
        c.validate_status()  # should not raise

    def test_invalid_status_raises(self):
        c = Contact(customer_name="Test", status="Inexistente")
        with pytest.raises(ValueError, match="Status inválido"):
            c.validate_status()

    def test_past_deadline_raises(self):
        c = Contact(
            customer_name="Test",
            deadline=date.today() - timedelta(days=1),
        )
        with pytest.raises(ValueError, match="não pode ser no passado"):
            c.validate_deadline_not_past()

    def test_today_deadline_passes(self):
        c = Contact(customer_name="Test", deadline=date.today())
        c.validate_deadline_not_past()  # should not raise
