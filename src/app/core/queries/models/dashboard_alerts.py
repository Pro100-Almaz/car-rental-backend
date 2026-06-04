from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class OverdueReturnAlertQm:
    rental_id: UUID
    vehicle_nickname: str | None
    license_plate: str
    client_name: str
    scheduled_end: datetime
    days_overdue: int


@dataclass(frozen=True, slots=True)
class ExpiringDocumentAlertQm:
    vehicle_id: UUID
    vehicle_nickname: str | None
    license_plate: str
    document_type: str
    expiry_date: date
    days_remaining: int


@dataclass(frozen=True, slots=True)
class ClientDebtAlertQm:
    client_id: UUID
    client_name: str
    phone: str
    debt_balance: str


@dataclass(frozen=True, slots=True)
class DashboardAlertsQm:
    overdue_returns: list[OverdueReturnAlertQm]
    expiring_documents: list[ExpiringDocumentAlertQm]
    clients_with_debt: list[ClientDebtAlertQm]
    total_alerts: int
