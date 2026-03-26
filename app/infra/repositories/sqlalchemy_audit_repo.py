"""SQLAlchemy implementation of AuditRepository."""

from __future__ import annotations

from app import db
from app.domain.entities.audit_log import AuditLog as DomainAuditLog
from app.models import AuditLog as AuditLogORM


class SqlAlchemyAuditRepository:
    """Concrete AuditRepository backed by SQLAlchemy."""

    @staticmethod
    def _to_domain(orm: AuditLogORM) -> DomainAuditLog:
        return DomainAuditLog(
            id=orm.id,
            user_id=orm.user_id,
            action=orm.action,
            target_type=orm.target_type,
            target_id=orm.target_id,
            details=orm.details,
            timestamp=orm.timestamp,
        )

    def save(self, entry: DomainAuditLog) -> DomainAuditLog:
        orm = AuditLogORM(
            user_id=entry.user_id,
            action=entry.action,
            target_type=entry.target_type,
            target_id=entry.target_id,
            details=entry.details,
        )
        db.session.add(orm)
        db.session.flush()
        entry.id = orm.id
        return entry

    def list_recent(
        self, page: int = 1, per_page: int = 30
    ) -> tuple[list[DomainAuditLog], int]:
        pagination = (
            AuditLogORM.query.order_by(AuditLogORM.timestamp.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        logs = [self._to_domain(x) for x in pagination.items]
        return logs, pagination.total

    def list_by_action(
        self, action: str, limit: int = 50
    ) -> list[DomainAuditLog]:
        orms = (
            AuditLogORM.query.filter_by(action=action)
            .order_by(AuditLogORM.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(x) for x in orms]
