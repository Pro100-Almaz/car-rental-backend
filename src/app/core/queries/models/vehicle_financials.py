from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class VehicleFinancialsQm:
    total_revenue: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    total_rentals: int
    days_rented: int
    days_in_period: int
    utilization_percent: Decimal
