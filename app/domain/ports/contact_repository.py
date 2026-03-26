"""Port: Contact Repository interface."""

from __future__ import annotations

from typing import Protocol

from app.domain.entities.contact import Contact


class ContactRepository(Protocol):
    """Abstract interface for contact persistence."""

    def get_by_id(self, contact_id: int) -> Contact | None: ...

    def get_by_id_for_user(
        self, contact_id: int, user_id: int, is_gestor: bool
    ) -> Contact | None: ...

    def save(self, contact: Contact) -> Contact: ...

    def update(self, contact: Contact) -> Contact: ...

    def delete(self, contact_id: int) -> None: ...

    def list_filtered(
        self,
        user_id: int | None,
        is_gestor: bool,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "deadline_asc",
        page: int = 1,
        per_page: int = 15,
    ) -> tuple[list[Contact], int]:
        """Return (contacts, total_count) for paginated listing."""
        ...

    def list_all(
        self,
        user_id: int | None,
        is_gestor: bool,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "deadline_asc",
    ) -> list[Contact]:
        """Return all contacts (unpaginated) for export."""
        ...

    def count_by_status(
        self, user_id: int | None, is_gestor: bool
    ) -> dict[str, int]: ...

    def count_overdue(self, user_id: int | None, is_gestor: bool) -> int: ...

    def count_inactive(
        self, user_id: int | None, is_gestor: bool, days: int
    ) -> int: ...

    def count_by_month(
        self, year: int, month: int, status: str | None = None
    ) -> int: ...

    def count_by_user_and_status(
        self, user_id: int, status: str
    ) -> int: ...

    def recent(
        self, user_id: int | None, is_gestor: bool, limit: int = 5
    ) -> list[Contact]: ...

    def save_bulk(self, contacts: list[Contact]) -> int:
        """Save multiple contacts; return count of saved."""
        ...
