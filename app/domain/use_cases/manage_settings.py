"""Use case for system settings management."""

from __future__ import annotations

from app.domain.ports.settings_repository import SettingsRepository
from app.domain.ports.audit_repository import AuditRepository
from app.domain.entities.audit_log import AuditLog


class GetSetting:
    def __init__(self, settings: SettingsRepository):
        self.settings = settings

    def execute(self, key: str, default: str = "") -> str:
        return self.settings.get(key, default)


class UpdateSetting:
    def __init__(
        self, settings: SettingsRepository, audits: AuditRepository
    ):
        self.settings = settings
        self.audits = audits

    def execute(
        self,
        key: str,
        value: str,
        user_id: int,
        description: str | None = None,
    ) -> None:
        self.settings.set(key, value, description)
        self.audits.save(
            AuditLog(
                user_id=user_id,
                action="alterou configuração",
                target_type="SystemSettings",
            )
        )
