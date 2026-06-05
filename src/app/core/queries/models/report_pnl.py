from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ExpenseCategoryLineQm:
    category_id: str | None
    category_name: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class CompanyPnlQm:
    period_from: str
    period_to: str
    total_revenue: Decimal
    returns_and_discounts: Decimal
    net_revenue: Decimal
    direct_expenses: list[ExpenseCategoryLineQm]
    total_direct_expenses: Decimal
    marginal_profit: Decimal
    overhead_expenses: list[ExpenseCategoryLineQm]
    total_overhead_expenses: Decimal
    operating_profit: Decimal
    taxes: Decimal
    net_profit: Decimal
    investor_payouts: Decimal
    retained_profit: Decimal
