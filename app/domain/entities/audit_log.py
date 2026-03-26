"""Pure domain entity for AuditLog — zero framework imports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AuditLog:
    user_id: int
    action: str
    target_type: str
    target_id: Optional[int] = None
    details: Optional[str] = None
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    id: Optional[int] = None
