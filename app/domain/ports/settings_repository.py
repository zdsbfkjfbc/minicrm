"""Port: Settings Repository interface."""

from __future__ import annotations

from typing import Protocol

from app.domain.entities.system_settings import SystemSettings


class SettingsRepository(Protocol):
    """Abstract interface for system settings persistence."""

    def get(self, key: str, default: str = "") -> str: ...

    def set(self, key: str, value: str, description: str | None = None) -> SystemSettings: ...
