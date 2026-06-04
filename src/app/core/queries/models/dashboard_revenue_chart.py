from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RevenueDataPointQm:
    date: str
    revenue: Decimal


@dataclass(frozen=True, slots=True)
class DashboardRevenueChartQm:
    period_from: str
    period_to: str
    data_points: list[RevenueDataPointQm]
    total: Decimal
