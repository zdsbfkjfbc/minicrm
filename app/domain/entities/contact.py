"""Pure domain entity for Contact — zero framework imports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional


from app.domain.entities.enums import ALLOWED_STATUSES, ContactStatus


@dataclass
class Contact:
    customer_name: str
    status: str = "Aberto"
    contact_type: str = "Pessoa"
    email: Optional[str] = None
    phone: Optional[str] = None
    deadline: Optional[date] = None
    observations: Optional[str] = None
    created_at: Optional[datetime] = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    user_id: Optional[int] = None
    owner_username: Optional[str] = None
    id: Optional[int] = None

    # ── Business rules ───────────────────────────────────────────────

    def is_overdue(self) -> bool:
        """Return True when the contact has an expired deadline and is not resolved."""
        if self.deadline and self.status != "Resolvido":
            return date.today() > self.deadline
        return False

    def validate_status(self) -> None:
        """Raise ValueError if the status is not in the allowed set."""
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(
                f"Status inválido: '{self.status}'. "
                f"Permitidos: {', '.join(sorted(ALLOWED_STATUSES))}"
            )

    def validate_deadline_not_past(self) -> None:
        """Raise ValueError if the deadline is in the past (creation-time rule)."""
        if self.deadline and self.deadline < date.today():
            raise ValueError("A Data Limite de Retorno não pode ser no passado.")
