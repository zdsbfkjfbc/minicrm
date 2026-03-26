"""Unit tests for DashboardMetrics use case — no Flask, no DB."""

import pytest
from datetime import date, timedelta, datetime, timezone

from app.domain.entities.contact import Contact
from app.domain.entities.user import User
from app.domain.use_cases.calculate_metrics import DashboardMetrics
from tests.unit.fakes import FakeContactRepository, FakeUserRepository


@pytest.fixture
def setup():
    contacts = FakeContactRepository()
    users = FakeUserRepository()

    op1 = users.save(User(username="op1", role="Operador"), "pass")
    op2 = users.save(User(username="op2", role="Operador"), "pass")

    # Create sample contacts
    for i in range(3):
        contacts.save(
            Contact(
                customer_name=f"Open{i}",
                status="Aberto",
                user_id=op1.id,
                deadline=date.today() + timedelta(days=1),
            )
        )
    contacts.save(
        Contact(
            customer_name="Resolved",
            status="Resolvido",
            user_id=op1.id,
        )
    )
    contacts.save(
        Contact(
            customer_name="Overdue",
            status="Aberto",
            user_id=op2.id,
            deadline=date.today() - timedelta(days=1),
        )
    )
    contacts.save(
        Contact(
            customer_name="Waiting",
            status="Aguardando Cliente",
            user_id=op2.id,
        )
    )

    return contacts, users


class TestIndexMetrics:
    def test_total_count(self, setup):
        contacts, users = setup
        dm = DashboardMetrics(contacts, users)
        result = dm.index_metrics(
            user_id=1, is_gestor=True, inactive_days=8
        )
        assert result["total"] == 6

    def test_overdue_count(self, setup):
        contacts, users = setup
        dm = DashboardMetrics(contacts, users)
        result = dm.index_metrics(
            user_id=1, is_gestor=True, inactive_days=8
        )
        assert result["overdue"] == 1

    def test_resolvidos_count(self, setup):
        contacts, users = setup
        dm = DashboardMetrics(contacts, users)
        result = dm.index_metrics(
            user_id=1, is_gestor=True, inactive_days=8
        )
        assert result["resolvidos"] == 1


class TestExportMetricsData:
    def test_has_sla_rate(self, setup):
        contacts, users = setup
        dm = DashboardMetrics(contacts, users)
        result = dm.export_metrics_data()
        assert "sla_rate" in result
        assert isinstance(result["sla_rate"], float)

    def test_has_operator_rows(self, setup):
        contacts, users = setup
        dm = DashboardMetrics(contacts, users)
        result = dm.export_metrics_data()
        assert len(result["op_rows"]) == 2  # 2 operators
