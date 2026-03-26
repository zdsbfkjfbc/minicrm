"""SQLAlchemy implementation of SettingsRepository."""

from __future__ import annotations

from app import db
from app.domain.entities.system_settings import (
    SystemSettings as DomainSettings,
)
from app.models import SystemSettings as SettingsORM


class SqlAlchemySettingsRepository:
    """Concrete SettingsRepository backed by SQLAlchemy."""

    def get(self, key: str, default: str = "") -> str:
        orm = SettingsORM.query.filter_by(key=key).first()
        return orm.value if orm else default

    def set(
        self, key: str, value: str, description: str | None = None
    ) -> DomainSettings:
        orm = SettingsORM.query.filter_by(key=key).first()
        if orm:
            orm.value = value
            if description is not None:
                orm.description = description
        else:
            orm = SettingsORM(key=key, value=value, description=description)
            db.session.add(orm)
        db.session.flush()
        return DomainSettings(
            id=orm.id, key=orm.key, value=orm.value, description=orm.description
        )
