from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class VehicleExpenseLineQm:
    category_name: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class VehicleComparisonItemQm:
    vehicle_id: UUID
    nickname: str | None
    license_plate: str
    total_revenue: Decimal
    expenses: list[VehicleExpenseLineQm]
    total_expenses: Decimal
    net_profit: Decimal
    utilization_percent: Decimal


@dataclass(frozen=True, slots=True)
class VehiclesComparisonQm:
    period_from: str
    period_to: str
    expense_categories: list[str]
    vehicles: list[VehicleComparisonItemQm]
