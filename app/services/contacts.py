from app.domain.use_cases.calculate_metrics import DashboardMetrics
from app.infra.repositories.sqlalchemy_contact_repo import (
    SqlAlchemyContactRepository,
)
from app.infra.repositories.sqlalchemy_user_repo import (
    SqlAlchemyUserRepository,
)


def _repos():
    return SqlAlchemyContactRepository(), SqlAlchemyUserRepository()


def dashboard_metrics(user):
    contacts, users = _repos()
    metrics = DashboardMetrics(contacts, users)
    return metrics.index_metrics(
        user_id=user.id,
        is_gestor=(user.role == 'Gestor'),
        inactive_days=8,
    )


def recent_contacts(user, limit=5):
    contacts, _ = _repos()
    return contacts.recent(
        user_id=user.id,
        is_gestor=(user.role == 'Gestor'),
        limit=limit,
    )
