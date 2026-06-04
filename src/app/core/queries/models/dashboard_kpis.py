from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class KpiValueQm:
    value: Decimal | int
    previous_value: Decimal | int
    change_percent: Decimal | None


@dataclass(frozen=True, slots=True)
class FleetStatusQm:
    available: int
    rented: int
    reserved: int
    in_service: int
    other: int
    total: int


@dataclass(frozen=True, slots=True)
class DashboardKpisQm:
    period_from: str
    period_to: str
    total_revenue: KpiValueQm
    total_expenses: KpiValueQm
    net_profit: KpiValueQm
    fleet_utilization: KpiValueQm
    active_rentals_count: KpiValueQm
    outstanding_debts: KpiValueQm
    fleet_status: FleetStatusQm
