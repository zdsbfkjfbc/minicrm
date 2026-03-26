"""Pure domain entity for User — zero framework imports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    username: str
    role: str = "Operador"
    id: Optional[int] = None

    # ── Business rules ───────────────────────────────────────────────

    def is_gestor(self) -> bool:
        return self.role == "Gestor"

    def is_operador(self) -> bool:
        return self.role == "Operador"

    def can_see_contact(self, contact_user_id: int | None) -> bool:
        """Gestores see everything; Operadores only their own."""
        if self.is_gestor():
            return True
        return self.id is not None and self.id == contact_user_id

    def require_role(self, role: str) -> None:
        """Raise PermissionError if user doesn't have the required role."""
        if self.role != role:
            raise PermissionError(
                f"Acesso negado. Requer papel '{role}', mas usuário é '{self.role}'."
            )
