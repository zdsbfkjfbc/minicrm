"""Unit tests for Contact CRUD use cases — no Flask, no DB."""

import pytest

from app.domain.use_cases.manage_contacts import (
    CreateContact,
    DeleteContact,
    GetContact,
    ListContacts,
    UpdateContact,
)
from tests.unit.fakes import FakeAuditRepository, FakeContactRepository


@pytest.fixture
def repos():
    return FakeContactRepository(), FakeAuditRepository()


class TestCreateContact:
    def test_creates_contact_with_id(self, repos):
        contacts, audits = repos
        uc = CreateContact(contacts, audits)
        result = uc.execute(
            customer_name="Empresa X", user_id=1, status="Aberto"
        )
        assert result.id == 1
        assert result.customer_name == "Empresa X"

    def test_creates_audit_log(self, repos):
        contacts, audits = repos
        uc = CreateContact(contacts, audits)
        uc.execute(customer_name="Empresa X", user_id=1)
        assert len(audits._store) == 1
        assert audits._store[0].action == "criou"

    def test_invalid_status_raises(self, repos):
        contacts, audits = repos
        uc = CreateContact(contacts, audits)
        with pytest.raises(ValueError, match="Status inválido"):
            uc.execute(
                customer_name="Test", user_id=1, status="Inexistente"
            )


class TestUpdateContact:
    def test_updates_contact(self, repos):
        contacts, audits = repos
        create = CreateContact(contacts, audits)
        created = create.execute(customer_name="Original", user_id=1)

        update = UpdateContact(contacts, audits)
        updated = update.execute(
            contact_id=created.id,
            user_id=1,
            is_gestor=True,
            customer_name="Updated",
            contact_type="Empresa",
            email="a@b.com",
            phone="123",
            status="Resolvido",
            observations="done",
        )
        assert updated.customer_name == "Updated"
        assert updated.status == "Resolvido"

    def test_update_nonexistent_raises(self, repos):
        contacts, audits = repos
        uc = UpdateContact(contacts, audits)
        with pytest.raises(PermissionError):
            uc.execute(
                contact_id=999,
                user_id=1,
                is_gestor=True,
                customer_name="X",
                contact_type="Pessoa",
                email=None,
                phone=None,
                status="Aberto",
                observations=None,
            )


class TestDeleteContact:
    def test_deletes_existing_contact(self, repos):
        contacts, audits = repos
        create = CreateContact(contacts, audits)
        created = create.execute(customer_name="ToDelete", user_id=1)

        delete = DeleteContact(contacts, audits)
        delete.execute(created.id, user_id=1, is_gestor=True)
        assert contacts.get_by_id(created.id) is None

    def test_delete_nonexistent_raises(self, repos):
        contacts, audits = repos
        uc = DeleteContact(contacts, audits)
        with pytest.raises(PermissionError):
            uc.execute(999, user_id=1, is_gestor=True)


class TestGetContact:
    def test_operador_cannot_see_others(self, repos):
        contacts, audits = repos
        create = CreateContact(contacts, audits)
        created = create.execute(customer_name="Other", user_id=2)

        get = GetContact(contacts)
        assert get.execute(created.id, user_id=1, is_gestor=False) is None

    def test_gestor_can_see_any(self, repos):
        contacts, audits = repos
        create = CreateContact(contacts, audits)
        created = create.execute(customer_name="Any", user_id=2)

        get = GetContact(contacts)
        assert get.execute(created.id, user_id=1, is_gestor=True) is not None


class TestListContacts:
    def test_returns_paginated(self, repos):
        contacts, audits = repos
        create = CreateContact(contacts, audits)
        for i in range(20):
            create.execute(customer_name=f"C{i}", user_id=1)

        ls = ListContacts(contacts)
        result, total = ls.execute(
            user_id=1, is_gestor=True, page=1, per_page=10
        )
        assert len(result) == 10
        assert total == 20
