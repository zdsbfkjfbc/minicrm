"""Domain entities — plain Python objects with business rules."""

from app.domain.entities.contact import Contact
from app.domain.entities.user import User
from app.domain.entities.audit_log import AuditLog
from app.domain.entities.system_settings import SystemSettings

__all__ = ["Contact", "User", "AuditLog", "SystemSettings"]
