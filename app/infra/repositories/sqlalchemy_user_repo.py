"""SQLAlchemy implementation of UserRepository."""

from __future__ import annotations

from app import db
from app.domain.entities.user import User as DomainUser
from app.models import User as UserORM


class SqlAlchemyUserRepository:
    """Concrete UserRepository backed by SQLAlchemy."""

    @staticmethod
    def _to_domain(orm: UserORM) -> DomainUser:
        return DomainUser(id=orm.id, username=orm.username, role=orm.role)

    def get_by_id(self, user_id: int) -> DomainUser | None:
        orm = db.session.get(UserORM, user_id)
        return self._to_domain(orm) if orm else None

    def get_by_username(self, username: str) -> DomainUser | None:
        orm = UserORM.query.filter_by(username=username).first()
        return self._to_domain(orm) if orm else None

    def save(self, user: DomainUser, password: str) -> DomainUser:
        orm = UserORM(username=user.username, role=user.role)
        orm.set_password(password)
        db.session.add(orm)
        db.session.flush()
        user.id = orm.id
        return user

    def check_password(self, user_id: int, password: str) -> bool:
        orm = db.session.get(UserORM, user_id)
        if not orm:
            return False
        return orm.check_password(password)

    def username_exists(self, username: str) -> bool:
        return (
            UserORM.query.filter_by(username=username).first() is not None
        )

    def list_operators(self) -> list[DomainUser]:
        return [
            self._to_domain(u)
            for u in UserORM.query.filter_by(role="Operador").all()
        ]
