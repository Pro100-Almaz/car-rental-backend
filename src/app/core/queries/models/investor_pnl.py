from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class InvestorVehiclePnlQm:
    vehicle_id: UUID
    share_percentage: Decimal
    total_revenue: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    investor_share: Decimal
    utilization_percent: Decimal


@dataclass(frozen=True, slots=True)
class InvestorPnlQm:
    investor_id: UUID
    period_from: str
    period_to: str
    total_revenue: Decimal
    total_expenses: Decimal
    total_net_profit: Decimal
    total_investor_share: Decimal
    vehicles: list[InvestorVehiclePnlQm]
