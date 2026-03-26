"""In-memory fake repositories for pure unit testing.

These fakes implement the same Protocol as the SQLAlchemy adapters
but store data in plain Python dicts/lists — no database needed.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.domain.entities.audit_log import AuditLog
from app.domain.entities.contact import Contact
from app.domain.entities.system_settings import SystemSettings
from app.domain.entities.user import User


class FakeContactRepository:
    def __init__(self):
        self._store: dict[int, Contact] = {}
        self._seq = 0

    def _next_id(self) -> int:
        self._seq += 1
        return self._seq

    def get_by_id(self, contact_id: int) -> Contact | None:
        return self._store.get(contact_id)

    def get_by_id_for_user(
        self, contact_id: int, user_id: int, is_gestor: bool
    ) -> Contact | None:
        c = self._store.get(contact_id)
        if not c:
            return None
        if is_gestor:
            return c
        return c if c.user_id == user_id else None

    def save(self, contact: Contact) -> Contact:
        contact.id = self._next_id()
        self._store[contact.id] = contact
        return contact

    def update(self, contact: Contact) -> Contact:
        if contact.id not in self._store:
            raise ValueError(f"Contact {contact.id} not found")
        self._store[contact.id] = contact
        return contact

    def delete(self, contact_id: int) -> None:
        self._store.pop(contact_id, None)

    def _filtered(self, user_id, is_gestor, status=None, search=None):
        items = list(self._store.values())
        if not is_gestor and user_id is not None:
            items = [c for c in items if c.user_id == user_id]
        if status and status != "Todos":
            items = [c for c in items if c.status == status]
        if search:
            items = [
                c for c in items
                if search.lower() in c.customer_name.lower()
            ]
        return items

    def list_filtered(
        self,
        user_id=None,
        is_gestor=True,
        status=None,
        search=None,
        sort_by="deadline_asc",
        page=1,
        per_page=15,
    ):
        items = self._filtered(user_id, is_gestor, status, search)
        total = len(items)
        start = (page - 1) * per_page
        return items[start : start + per_page], total

    def list_all(
        self,
        user_id=None,
        is_gestor=True,
        status=None,
        search=None,
        sort_by="deadline_asc",
    ):
        return self._filtered(user_id, is_gestor, status, search)

    def count_by_status(self, user_id, is_gestor):
        items = self._filtered(user_id, is_gestor)
        return {
            "total": len(items),
            "abertos": sum(1 for c in items if c.status == "Aberto"),
            "aguardando": sum(
                1 for c in items if c.status == "Aguardando Cliente"
            ),
            "resolvidos": sum(1 for c in items if c.status == "Resolvido"),
            "cancelados": sum(1 for c in items if c.status == "Cancelado"),
            "pendentes": sum(
                1 for c in items if c.status != "Resolvido"
            ),
        }

    def count_overdue(self, user_id, is_gestor):
        items = self._filtered(user_id, is_gestor)
        today = date.today()
        return sum(
            1 for c in items
            if c.deadline
            and c.deadline < today
            and c.status not in ("Resolvido", "Cancelado")
        )

    def count_inactive(self, user_id, is_gestor, days):
        items = self._filtered(user_id, is_gestor)
        threshold = datetime.now(timezone.utc) - timedelta(days=days)
        return sum(
            1 for c in items
            if c.created_at
            and c.created_at <= threshold
            and c.status not in ("Resolvido", "Cancelado")
        )

    def count_by_month(self, year, month, status=None):
        items = list(self._store.values())
        if status:
            items = [c for c in items if c.status == status]
        return sum(
            1 for c in items
            if c.created_at
            and c.created_at.year == year
            and c.created_at.month == month
        )

    def count_by_user_and_status(self, user_id, status):
        return sum(
            1 for c in self._store.values()
            if c.user_id == user_id and c.status == status
        )

    def recent(self, user_id, is_gestor, limit=5):
        items = self._filtered(user_id, is_gestor)
        items.sort(
            key=lambda c: c.created_at or datetime.min.replace(
                tzinfo=timezone.utc
            ),
            reverse=True,
        )
        return items[:limit]

    def save_bulk(self, contacts):
        for c in contacts:
            self.save(c)
        return len(contacts)


class FakeUserRepository:
    def __init__(self):
        self._store: dict[int, tuple[User, str]] = {}
        self._seq = 0

    def _next_id(self) -> int:
        self._seq += 1
        return self._seq

    def get_by_id(self, user_id: int) -> User | None:
        entry = self._store.get(user_id)
        return entry[0] if entry else None

    def get_by_username(self, username: str) -> User | None:
        for user, _ in self._store.values():
            if user.username == username:
                return user
        return None

    def save(self, user: User, password: str) -> User:
        user.id = self._next_id()
        self._store[user.id] = (user, password)
        return user

    def check_password(self, user_id: int, password: str) -> bool:
        entry = self._store.get(user_id)
        if not entry:
            return False
        return entry[1] == password

    def username_exists(self, username: str) -> bool:
        return self.get_by_username(username) is not None

    def list_operators(self) -> list[User]:
        return [u for u, _ in self._store.values() if u.role == "Operador"]


class FakeAuditRepository:
    def __init__(self):
        self._store: list[AuditLog] = []
        self._seq = 0

    def save(self, entry: AuditLog) -> AuditLog:
        self._seq += 1
        entry.id = self._seq
        self._store.append(entry)
        return entry

    def list_recent(self, page=1, per_page=30):
        items = sorted(
            self._store, key=lambda x: x.timestamp, reverse=True
        )
        total = len(items)
        start = (page - 1) * per_page
        return items[start : start + per_page], total

    def list_by_action(self, action, limit=50):
        items = [x for x in self._store if x.action == action]
        items.sort(key=lambda x: x.timestamp, reverse=True)
        return items[:limit]


class FakeSettingsRepository:
    def __init__(self):
        self._store: dict[str, SystemSettings] = {}

    def get(self, key: str, default: str = "") -> str:
        s = self._store.get(key)
        return s.value if s else default

    def set(self, key, value, description=None):
        s = self._store.get(key)
        if s:
            s.value = value
            if description is not None:
                s.description = description
        else:
            s = SystemSettings(key=key, value=value, description=description)
            self._store[key] = s
        return s
