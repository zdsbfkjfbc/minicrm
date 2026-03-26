"""SQLAlchemy implementation of ContactRepository."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app import db
from app.domain.entities.contact import Contact as DomainContact
from app.models import Contact as ContactORM


class SqlAlchemyContactRepository:
    """Concrete ContactRepository backed by SQLAlchemy."""

    # ── Mappers ──────────────────────────────────────────────────────

    @staticmethod
    def _to_domain(orm: ContactORM) -> DomainContact:
        return DomainContact(
            id=orm.id,
            customer_name=orm.customer_name,
            contact_type=orm.contact_type or "Pessoa",
            email=orm.email,
            phone=orm.phone,
            status=orm.status,
            deadline=orm.deadline,
            observations=orm.observations,
            created_at=orm.created_at,
            user_id=orm.user_id,
            owner_username=orm.owner.username if orm.owner else None,
        )

    @staticmethod
    def _apply_user_filter(query, user_id, is_gestor):
        if not is_gestor and user_id is not None:
            query = query.filter_by(user_id=user_id)
        return query

    # ── CRUD ─────────────────────────────────────────────────────────

    def get_by_id(self, contact_id: int) -> DomainContact | None:
        orm = db.session.get(ContactORM, contact_id)
        return self._to_domain(orm) if orm else None

    def get_by_id_for_user(
        self, contact_id: int, user_id: int, is_gestor: bool
    ) -> DomainContact | None:
        if is_gestor:
            orm = db.session.get(ContactORM, contact_id)
        else:
            orm = ContactORM.query.filter_by(
                id=contact_id, user_id=user_id
            ).first()
        return self._to_domain(orm) if orm else None

    def save(self, contact: DomainContact) -> DomainContact:
        orm = ContactORM(
            customer_name=contact.customer_name,
            contact_type=contact.contact_type,
            email=contact.email,
            phone=contact.phone,
            status=contact.status,
            deadline=contact.deadline,
            observations=contact.observations,
            user_id=contact.user_id,
        )
        db.session.add(orm)
        db.session.flush()
        contact.id = orm.id
        return contact

    def update(self, contact: DomainContact) -> DomainContact:
        orm = db.session.get(ContactORM, contact.id)
        if not orm:
            raise ValueError(f"Contact {contact.id} not found")
        orm.customer_name = contact.customer_name
        orm.contact_type = contact.contact_type
        orm.email = contact.email
        orm.phone = contact.phone
        orm.status = contact.status
        orm.deadline = contact.deadline
        orm.observations = contact.observations
        db.session.flush()
        return contact

    def delete(self, contact_id: int) -> None:
        orm = db.session.get(ContactORM, contact_id)
        if orm:
            db.session.delete(orm)
            db.session.flush()

    # ── Listing ──────────────────────────────────────────────────────

    def _build_base_query(self, user_id, is_gestor, status=None, search=None):
        query = ContactORM.query
        query = self._apply_user_filter(query, user_id, is_gestor)
        if status and status != "Todos":
            query = query.filter_by(status=status)
        if search:
            query = query.filter(
                ContactORM.customer_name.ilike(f"%{search}%")
            )
        return query

    @staticmethod
    def _apply_sort(query, sort_by):
        if sort_by == "deadline_desc":
            return query.order_by(ContactORM.deadline.desc())
        if sort_by == "created_desc":
            return query.order_by(ContactORM.created_at.desc())
        if sort_by == "deadline_asc":
            return query.order_by(ContactORM.deadline.asc())
        return query.order_by(ContactORM.deadline.asc())

    def list_filtered(
        self,
        user_id: int | None,
        is_gestor: bool,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "deadline_asc",
        page: int = 1,
        per_page: int = 15,
    ) -> tuple[list[DomainContact], int]:
        query = self._build_base_query(user_id, is_gestor, status, search)
        query = self._apply_sort(query, sort_by)
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        contacts = [self._to_domain(c) for c in pagination.items]
        return contacts, pagination.total

    def list_all(
        self,
        user_id: int | None,
        is_gestor: bool,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "deadline_asc",
    ) -> list[DomainContact]:
        query = self._build_base_query(user_id, is_gestor, status, search)
        query = self._apply_sort(query, sort_by)
        return [self._to_domain(c) for c in query.all()]

    # ── Aggregations ─────────────────────────────────────────────────

    def count_by_status(
        self, user_id: int | None, is_gestor: bool
    ) -> dict[str, int]:
        base = ContactORM.query
        base = self._apply_user_filter(base, user_id, is_gestor)
        return {
            "total": base.count(),
            "abertos": base.filter_by(status="Aberto").count(),
            "aguardando": base.filter_by(status="Aguardando Cliente").count(),
            "resolvidos": base.filter_by(status="Resolvido").count(),
            "cancelados": base.filter_by(status="Cancelado").count(),
            "pendentes": base.filter(
                ContactORM.status != "Resolvido"
            ).count(),
        }

    def count_overdue(self, user_id: int | None, is_gestor: bool) -> int:
        from datetime import date

        base = ContactORM.query
        base = self._apply_user_filter(base, user_id, is_gestor)
        return base.filter(
            ContactORM.status.notin_(["Resolvido", "Cancelado"]),
            ContactORM.deadline < date.today(),
        ).count()

    def count_inactive(
        self, user_id: int | None, is_gestor: bool, days: int
    ) -> int:
        threshold = datetime.now(timezone.utc) - timedelta(days=days)
        base = ContactORM.query
        base = self._apply_user_filter(base, user_id, is_gestor)
        return base.filter(
            ContactORM.status.notin_(["Resolvido", "Cancelado"]),
            ContactORM.created_at <= threshold,
        ).count()

    def count_by_month(
        self, year: int, month: int, status: str | None = None
    ) -> int:
        query = ContactORM.query.filter(
            db.extract("year", ContactORM.created_at) == year,
            db.extract("month", ContactORM.created_at) == month,
        )
        if status:
            query = query.filter_by(status=status)
        return query.count()

    def count_by_user_and_status(self, user_id: int, status: str) -> int:
        return ContactORM.query.filter_by(
            user_id=user_id, status=status
        ).count()

    def recent(
        self, user_id: int | None, is_gestor: bool, limit: int = 5
    ) -> list[DomainContact]:
        base = ContactORM.query
        base = self._apply_user_filter(base, user_id, is_gestor)
        return [
            self._to_domain(c)
            for c in base.order_by(ContactORM.created_at.desc())
            .limit(limit)
            .all()
        ]

    def save_bulk(self, contacts: list[DomainContact]) -> int:
        orm_objects = [
            ContactORM(
                customer_name=c.customer_name,
                contact_type=c.contact_type,
                email=c.email,
                phone=c.phone,
                status=c.status,
                deadline=c.deadline,
                observations=c.observations,
                user_id=c.user_id,
            )
            for c in contacts
        ]
        db.session.add_all(orm_objects)
        db.session.flush()
        return len(orm_objects)
