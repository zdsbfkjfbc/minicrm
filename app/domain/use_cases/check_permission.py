"""Use case for permission checks — pure functions, no framework."""

from __future__ import annotations

from app.domain.entities.user import User


def require_gestor(user: User) -> None:
    """Raise PermissionError if user is not a Gestor."""
    user.require_role("Gestor")


def can_access_contact(
    user: User, contact_user_id: int | None
) -> bool:
    """Return True if user can access a contact owned by contact_user_id."""
    return user.can_see_contact(contact_user_id)
