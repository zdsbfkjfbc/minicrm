"""Use cases for Contact CRUD — testable without any framework."""

from __future__ import annotations

from app.domain.entities.contact import Contact
from app.domain.entities.audit_log import AuditLog
from app.domain.ports.contact_repository import ContactRepository
from app.domain.ports.audit_repository import AuditRepository


class CreateContact:
    def __init__(self, contacts: ContactRepository, audits: AuditRepository):
        self.contacts = contacts
        self.audits = audits

    def execute(
        self,
        customer_name: str,
        user_id: int,
        contact_type: str = "Pessoa",
        email: str | None = None,
        phone: str | None = None,
        status: str = "Aberto",
        deadline: date | None = None,
        observations: str | None = None,
    ) -> Contact:
        contact = Contact(
            customer_name=customer_name,
            contact_type=contact_type,
            email=email,
            phone=phone,
            status=status,
            deadline=deadline,
            observations=observations,
            user_id=user_id,
        )
        contact.validate_status()
        saved = self.contacts.save(contact)
        self.audits.save(
            AuditLog(
                user_id=user_id,
                action="criou",
                target_type="Contact",
                target_id=saved.id,
            )
        )
        return saved


class UpdateContact:
    def __init__(self, contacts: ContactRepository, audits: AuditRepository):
        self.contacts = contacts
        self.audits = audits

    def execute(
        self,
        contact_id: int,
        user_id: int,
        is_gestor: bool,
        *,
        customer_name: str,
        contact_type: str,
        email: str | None,
        phone: str | None,
        status: str,
        deadline=None,
        observations: str | None,
    ) -> Contact:
        existing = self.contacts.get_by_id_for_user(
            contact_id, user_id, is_gestor
        )
        if not existing:
            raise PermissionError("Contato não encontrado ou acesso negado.")

        old_status = existing.status
        existing.customer_name = customer_name
        existing.contact_type = contact_type
        existing.email = email
        existing.phone = phone
        existing.status = status
        existing.deadline = deadline
        existing.observations = observations
        existing.validate_status()

        updated = self.contacts.update(existing)
        details = (
            f"{old_status} → {status}" if old_status != status else None
        )
        self.audits.save(
            AuditLog(
                user_id=user_id,
                action="editou",
                target_type="Contact",
                target_id=contact_id,
                details=details,
            )
        )
        return updated


class DeleteContact:
    def __init__(self, contacts: ContactRepository, audits: AuditRepository):
        self.contacts = contacts
        self.audits = audits

    def execute(
        self, contact_id: int, user_id: int, is_gestor: bool
    ) -> None:
        existing = self.contacts.get_by_id_for_user(
            contact_id, user_id, is_gestor
        )
        if not existing:
            raise PermissionError("Contato não encontrado ou acesso negado.")

        self.audits.save(
            AuditLog(
                user_id=user_id,
                action="excluiu",
                target_type="Contact",
                target_id=contact_id,
            )
        )
        self.contacts.delete(contact_id)


class GetContact:
    def __init__(self, contacts: ContactRepository):
        self.contacts = contacts

    def execute(
        self, contact_id: int, user_id: int, is_gestor: bool
    ) -> Contact | None:
        return self.contacts.get_by_id_for_user(
            contact_id, user_id, is_gestor
        )


class ListContacts:
    def __init__(self, contacts: ContactRepository):
        self.contacts = contacts

    def execute(
        self,
        user_id: int,
        is_gestor: bool,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "deadline_asc",
        page: int = 1,
        per_page: int = 15,
    ) -> tuple[list[Contact], int]:
        return self.contacts.list_filtered(
            user_id=user_id if not is_gestor else None,
            is_gestor=is_gestor,
            status=status,
            search=search,
            sort_by=sort_by,
            page=page,
            per_page=per_page,
        )
