from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CashFlowDayQm:
    date: str
    income: Decimal
    expense: Decimal
    net: Decimal


@dataclass(frozen=True, slots=True)
class CashFlowQm:
    period_from: str
    period_to: str
    opening_balance: Decimal
    total_income: Decimal
    total_expense: Decimal
    closing_balance: Decimal
    daily_breakdown: list[CashFlowDayQm]
