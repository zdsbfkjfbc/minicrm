"""Use cases for dashboard metrics calculation — testable without any framework."""

from __future__ import annotations

from datetime import date

from app.domain.ports.contact_repository import ContactRepository
from app.domain.ports.user_repository import UserRepository


class DashboardMetrics:
    """Calculate all metrics needed by the index and dashboard pages."""

    def __init__(
        self, contacts: ContactRepository, users: UserRepository
    ):
        self.contacts = contacts
        self.users = users

    def index_metrics(
        self, user_id: int, is_gestor: bool, inactive_days: int
    ) -> dict:
        uid = user_id if not is_gestor else None
        counts = self.contacts.count_by_status(uid, is_gestor)
        overdue = self.contacts.count_overdue(uid, is_gestor)
        inactive = self.contacts.count_inactive(uid, is_gestor, inactive_days)
        return {
            "total": counts["total"],
            "pendentes": counts["pendentes"],
            "resolvidos": counts["resolvidos"],
            "overdue": overdue,
            "inactive": inactive,
            "inactive_days": inactive_days,
        }

    def dashboard_full(self) -> dict:
        """Full metrics for the Gestor dashboard page."""
        counts = self.contacts.count_by_status(None, True)
        overdue = self.contacts.count_overdue(None, True)

        # Monthly data (last 6 months)
        today = date.today()
        months = []
        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            months.append((m, y))

        month_names = [
            "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez",
        ]
        monthly_labels = [
            f"{month_names[m - 1]}/{str(y)[-2:]}" for m, y in months
        ]
        monthly_values = [
            self.contacts.count_by_month(y, m) for m, y in months
        ]
        monthly_abertos = [
            self.contacts.count_by_month(y, m, "Aberto") for m, y in months
        ]
        monthly_resolvidos = [
            self.contacts.count_by_month(y, m, "Resolvido")
            for m, y in months
        ]

        # Operator breakdown
        operators = self.users.list_operators()
        operator_names = [u.username for u in operators]
        op_statuses = [
            "Aberto",
            "Aguardando Cliente",
            "Resolvido",
            "Cancelado",
        ]
        op_colors = ["#3b82f6", "#f97316", "#22c55e", "#9ca3af"]
        operator_series = []
        for s in op_statuses:
            data = [
                self.contacts.count_by_user_and_status(u.id, s)
                for u in operators
            ]
            operator_series.append({"name": s, "data": data})

        # SLA
        active = counts["total"] - counts["resolvidos"] - counts["cancelados"]
        sla_rate = (
            round((1 - overdue / active) * 100, 1) if active > 0 else 100.0
        )

        return {
            "metrics": counts | {"overdue": overdue},
            "monthly_labels": monthly_labels,
            "monthly_values": monthly_values,
            "donut_data": [
                counts["abertos"],
                counts["aguardando"],
                counts["resolvidos"],
                counts["cancelados"],
            ],
            "monthly_abertos": monthly_abertos,
            "monthly_resolvidos": monthly_resolvidos,
            "operator_names": operator_names,
            "operator_series": operator_series,
            "op_colors": op_colors,
            "sla_rate": sla_rate,
        }

    def export_metrics_data(self) -> dict:
        """Data needed by the metrics export (CSV/XLSX/PDF)."""
        counts = self.contacts.count_by_status(None, True)
        overdue = self.contacts.count_overdue(None, True)
        active = counts["total"] - counts["resolvidos"] - counts["cancelados"]
        sla_rate = (
            round((1 - overdue / active) * 100, 1) if active > 0 else 100.0
        )

        operators = self.users.list_operators()
        op_rows = []
        for u in operators:
            op_rows.append([
                u.username,
                self.contacts.count_by_user_and_status(u.id, "Aberto"),
                self.contacts.count_by_user_and_status(
                    u.id, "Aguardando Cliente"
                ),
                self.contacts.count_by_user_and_status(u.id, "Resolvido"),
                self.contacts.count_by_user_and_status(u.id, "Cancelado"),
            ])

        return {
            "total": counts["total"],
            "abertos": counts["abertos"],
            "aguardando": counts["aguardando"],
            "resolvidos": counts["resolvidos"],
            "cancelados": counts["cancelados"],
            "overdue": overdue,
            "sla_rate": sla_rate,
            "op_rows": op_rows,
        }
