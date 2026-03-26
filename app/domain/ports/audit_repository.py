"""Port: Audit Repository interface."""

from __future__ import annotations

from typing import Protocol

from app.domain.entities.audit_log import AuditLog


class AuditRepository(Protocol):
    """Abstract interface for audit-log persistence."""

    def save(self, entry: AuditLog) -> AuditLog: ...

    def list_recent(
        self, page: int = 1, per_page: int = 30
    ) -> tuple[list[AuditLog], int]:
        """Return (logs, total_count) paginated."""
        ...

    def list_by_action(
        self, action: str, limit: int = 50
    ) -> list[AuditLog]: ...
