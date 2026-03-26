"""Port: User Repository interface."""

from __future__ import annotations

from typing import Protocol

from app.domain.entities.user import User


class UserRepository(Protocol):
    """Abstract interface for user persistence."""

    def get_by_id(self, user_id: int) -> User | None: ...

    def get_by_username(self, username: str) -> User | None: ...

    def save(self, user: User, password: str) -> User: ...

    def check_password(self, user_id: int, password: str) -> bool: ...

    def list_operators(self) -> list[User]: ...
