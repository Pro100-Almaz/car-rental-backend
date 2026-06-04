from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from collections import defaultdict

from sqlalchemy import and_, case, func, outerjoin, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.report_cash_flow import CashFlowDayQm, CashFlowQm
from app.core.queries.models.report_pnl import CompanyPnlQm, ExpenseCategoryLineQm
from app.core.queries.models.report_vehicles_comparison import (
    VehicleComparisonItemQm,
    VehicleExpenseLineQm,
    VehiclesComparisonQm,
)
from app.core.queries.ports.report_reader import ReportReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.cash_journal_entry import cash_journal_table
from app.infrastructure.persistence_sqla.mappings.expense_category import expense_categories_table
from app.infrastructure.persistence_sqla.mappings.investor_payout import investor_payouts_table
from app.infrastructure.persistence_sqla.mappings.rental import rentals_table
from app.infrastructure.persistence_sqla.mappings.vehicle import vehicles_table


class SqlaReportReader(ReportReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_company_pnl(
        self,
        *,
        organization_id: UUID,
        date_from: date,
        date_to: date,
    ) -> CompanyPnlQm:
        try:
            total_revenue = await self._get_revenue(organization_id, date_from, date_to)
            direct_expenses = await self._get_expenses_by_type(organization_id, date_from, date_to, "direct")
            overhead_expenses = await self._get_expenses_by_type(organization_id, date_from, date_to, "overhead")
            taxes = await self._get_tax_expenses(organization_id, date_from, date_to)
            investor_payouts = await self._get_investor_payouts(organization_id, date_from, date_to)
        except SQLAlchemyError as e:
            raise ReaderError from e

        returns_and_discounts = Decimal(0)
        net_revenue = total_revenue - returns_and_discounts

        total_direct = sum(e.amount for e in direct_expenses)
        marginal_profit = net_revenue - total_direct

        total_overhead = sum(e.amount for e in overhead_expenses)
        operating_profit = marginal_profit - total_overhead

        net_profit = operating_profit - taxes
        retained_profit = net_profit - investor_payouts

        return CompanyPnlQm(
            period_from=date_from.isoformat(),
            period_to=date_to.isoformat(),
            total_revenue=total_revenue,
            returns_and_discounts=returns_and_discounts,
            net_revenue=net_revenue,
            direct_expenses=direct_expenses,
            total_direct_expenses=total_direct,
            marginal_profit=marginal_profit,
            overhead_expenses=overhead_expenses,
            total_overhead_expenses=total_overhead,
            operating_profit=operating_profit,
            taxes=taxes,
            net_profit=net_profit,
            investor_payouts=investor_payouts,
            retained_profit=retained_profit,
        )

    async def _get_revenue(
        self, organization_id: UUID, date_from: date, date_to: date,
    ) -> Decimal:
        stmt = select(
            func.coalesce(func.sum(cash_journal_table.c.amount), Decimal(0)),
        ).where(
            and_(
                cash_journal_table.c.organization_id == organization_id,
                cash_journal_table.c.operation_type == "income",
                cash_journal_table.c.date >= date_from,
                cash_journal_table.c.date <= date_to,
            ),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or Decimal(0)

    async def _get_expenses_by_type(
        self,
        organization_id: UUID,
        date_from: date,
        date_to: date,
        category_type: str,
    ) -> list[ExpenseCategoryLineQm]:
        j = outerjoin(
            cash_journal_table,
            expense_categories_table,
            cash_journal_table.c.expense_category_id == expense_categories_table.c.id,
        )
        stmt = (
            select(
                expense_categories_table.c.id.label("category_id"),
                expense_categories_table.c.name.label("category_name"),
                func.coalesce(func.sum(cash_journal_table.c.amount), Decimal(0)).label("amount"),
            )
            .select_from(j)
            .where(
                and_(
                    cash_journal_table.c.organization_id == organization_id,
                    cash_journal_table.c.operation_type == "expense",
                    cash_journal_table.c.date >= date_from,
                    cash_journal_table.c.date <= date_to,
                    expense_categories_table.c.type == category_type,
                ),
            )
            .group_by(expense_categories_table.c.id, expense_categories_table.c.name)
            .order_by(expense_categories_table.c.name)
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        return [
            ExpenseCategoryLineQm(
                category_id=str(row.category_id) if row.category_id else None,
                category_name=row.category_name or "Uncategorized",
                amount=row.amount,
            )
            for row in rows
        ]

    async def _get_tax_expenses(
        self, organization_id: UUID, date_from: date, date_to: date,
    ) -> Decimal:
        j = outerjoin(
            cash_journal_table,
            expense_categories_table,
            cash_journal_table.c.expense_category_id == expense_categories_table.c.id,
        )
        stmt = select(
            func.coalesce(func.sum(cash_journal_table.c.amount), Decimal(0)),
        ).select_from(j).where(
            and_(
                cash_journal_table.c.organization_id == organization_id,
                cash_journal_table.c.operation_type == "expense",
                cash_journal_table.c.date >= date_from,
                cash_journal_table.c.date <= date_to,
                func.lower(expense_categories_table.c.name) == "taxes",
            ),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or Decimal(0)

    async def _get_investor_payouts(
        self, organization_id: UUID, date_from: date, date_to: date,
    ) -> Decimal:
        stmt = select(
            func.coalesce(func.sum(investor_payouts_table.c.share_amount), Decimal(0)),
        ).where(
            and_(
                investor_payouts_table.c.organization_id == organization_id,
                investor_payouts_table.c.status == "paid",
                investor_payouts_table.c.period_month >= date_from,
                investor_payouts_table.c.period_month <= date_to,
            ),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or Decimal(0)

    async def get_cash_flow(
        self,
        *,
        organization_id: UUID,
        date_from: date,
        date_to: date,
    ) -> CashFlowQm:
        try:
            opening_balance = await self._get_balance_before(organization_id, date_from)
            daily = await self._get_daily_breakdown(organization_id, date_from, date_to)
        except SQLAlchemyError as e:
            raise ReaderError from e

        total_income = sum(d.income for d in daily)
        total_expense = sum(d.expense for d in daily)
        closing_balance = opening_balance + total_income - total_expense

        return CashFlowQm(
            period_from=date_from.isoformat(),
            period_to=date_to.isoformat(),
            opening_balance=opening_balance,
            total_income=total_income,
            total_expense=total_expense,
            closing_balance=closing_balance,
            daily_breakdown=daily,
        )

    async def _get_balance_before(
        self, organization_id: UUID, before_date: date,
    ) -> Decimal:
        income_sum = func.coalesce(
            func.sum(
                case(
                    (cash_journal_table.c.operation_type == "income", cash_journal_table.c.amount),
                    else_=Decimal(0),
                )
            ),
            Decimal(0),
        )
        expense_sum = func.coalesce(
            func.sum(
                case(
                    (cash_journal_table.c.operation_type == "expense", cash_journal_table.c.amount),
                    else_=Decimal(0),
                )
            ),
            Decimal(0),
        )
        stmt = select(
            (income_sum - expense_sum).label("balance"),
        ).where(
            and_(
                cash_journal_table.c.organization_id == organization_id,
                cash_journal_table.c.date < before_date,
            ),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or Decimal(0)

    async def _get_daily_breakdown(
        self, organization_id: UUID, date_from: date, date_to: date,
    ) -> list[CashFlowDayQm]:
        income_col = func.coalesce(
            func.sum(
                case(
                    (cash_journal_table.c.operation_type == "income", cash_journal_table.c.amount),
                    else_=Decimal(0),
                )
            ),
            Decimal(0),
        ).label("income")
        expense_col = func.coalesce(
            func.sum(
                case(
                    (cash_journal_table.c.operation_type == "expense", cash_journal_table.c.amount),
                    else_=Decimal(0),
                )
            ),
            Decimal(0),
        ).label("expense")
        stmt = (
            select(
                cash_journal_table.c.date.label("day"),
                income_col,
                expense_col,
            )
            .where(
                and_(
                    cash_journal_table.c.organization_id == organization_id,
                    cash_journal_table.c.date >= date_from,
                    cash_journal_table.c.date <= date_to,
                ),
            )
            .group_by(cash_journal_table.c.date)
            .order_by(cash_journal_table.c.date)
        )
        result = await self._session.execute(stmt)
        return [
            CashFlowDayQm(
                date=row.day.isoformat(),
                income=row.income,
                expense=row.expense,
                net=row.income - row.expense,
            )
            for row in result.all()
        ]

    async def get_vehicles_comparison(
        self,
        *,
        organization_id: UUID,
        date_from: date,
        date_to: date,
    ) -> VehiclesComparisonQm:
        try:
            vehicles = await self._get_org_vehicles(organization_id)
            all_categories = await self._get_active_direct_categories(organization_id)
            category_names = [c["name"] for c in all_categories]

            items: list[VehicleComparisonItemQm] = []
            for v in vehicles:
                revenue = await self._get_vehicle_revenue(v["id"], date_from, date_to)
                expenses_map = await self._get_vehicle_expenses_by_category(v["id"], date_from, date_to)
                utilization = await self._get_vehicle_utilization(v["id"], date_from, date_to)

                expense_lines = [
                    VehicleExpenseLineQm(
                        category_name=name,
                        amount=expenses_map.get(name, Decimal(0)),
                    )
                    for name in category_names
                ]
                total_exp = sum(e.amount for e in expense_lines)

                items.append(
                    VehicleComparisonItemQm(
                        vehicle_id=v["id"],
                        nickname=v["nickname"],
                        license_plate=v["license_plate"],
                        total_revenue=revenue,
                        expenses=expense_lines,
                        total_expenses=total_exp,
                        net_profit=revenue - total_exp,
                        utilization_percent=utilization,
                    )
                )
        except SQLAlchemyError as e:
            raise ReaderError from e

        return VehiclesComparisonQm(
            period_from=date_from.isoformat(),
            period_to=date_to.isoformat(),
            expense_categories=category_names,
            vehicles=items,
        )

    async def _get_org_vehicles(self, organization_id: UUID) -> list[dict]:
        stmt = (
            select(
                vehicles_table.c.id,
                vehicles_table.c.nickname,
                vehicles_table.c.license_plate,
            )
            .where(vehicles_table.c.organization_id == organization_id)
            .order_by(vehicles_table.c.nickname)
        )
        result = await self._session.execute(stmt)
        return [
            {"id": row.id, "nickname": row.nickname, "license_plate": row.license_plate}
            for row in result.all()
        ]

    async def _get_active_direct_categories(self, organization_id: UUID) -> list[dict]:
        stmt = (
            select(
                expense_categories_table.c.id,
                expense_categories_table.c.name,
            )
            .where(
                and_(
                    expense_categories_table.c.organization_id == organization_id,
                    expense_categories_table.c.type == "direct",
                    expense_categories_table.c.is_active.is_(True),
                ),
            )
            .order_by(expense_categories_table.c.sort_order)
        )
        result = await self._session.execute(stmt)
        return [{"id": row.id, "name": row.name} for row in result.all()]

    async def _get_vehicle_revenue(
        self, vehicle_id: UUID, date_from: date, date_to: date,
    ) -> Decimal:
        stmt = select(
            func.coalesce(func.sum(cash_journal_table.c.amount), Decimal(0)),
        ).where(
            and_(
                cash_journal_table.c.vehicle_id == vehicle_id,
                cash_journal_table.c.operation_type == "income",
                cash_journal_table.c.date >= date_from,
                cash_journal_table.c.date <= date_to,
            ),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or Decimal(0)

    async def _get_vehicle_expenses_by_category(
        self, vehicle_id: UUID, date_from: date, date_to: date,
    ) -> dict[str, Decimal]:
        j = outerjoin(
            cash_journal_table,
            expense_categories_table,
            cash_journal_table.c.expense_category_id == expense_categories_table.c.id,
        )
        stmt = (
            select(
                expense_categories_table.c.name.label("category_name"),
                func.coalesce(func.sum(cash_journal_table.c.amount), Decimal(0)).label("amount"),
            )
            .select_from(j)
            .where(
                and_(
                    cash_journal_table.c.vehicle_id == vehicle_id,
                    cash_journal_table.c.operation_type == "expense",
                    cash_journal_table.c.date >= date_from,
                    cash_journal_table.c.date <= date_to,
                ),
            )
            .group_by(expense_categories_table.c.name)
        )
        result = await self._session.execute(stmt)
        return {row.category_name or "Uncategorized": row.amount for row in result.all()}

    async def _get_vehicle_utilization(
        self, vehicle_id: UUID, date_from: date, date_to: date,
    ) -> Decimal:
        days_in_period = max((date_to - date_from).days, 1)
        stmt = select(
            func.coalesce(
                func.sum(
                    func.least(
                        func.coalesce(
                            func.date(rentals_table.c.actual_end),
                            func.date(rentals_table.c.scheduled_end),
                        ),
                        date_to,
                    )
                    - func.greatest(
                        func.date(rentals_table.c.actual_start),
                        date_from,
                    )
                    + 1
                ),
                0,
            ).label("days_rented"),
        ).where(
            and_(
                rentals_table.c.vehicle_id == vehicle_id,
                rentals_table.c.status.in_(["active", "returning", "completed"]),
                rentals_table.c.actual_start.isnot(None),
                func.date(rentals_table.c.actual_start) <= date_to,
                func.coalesce(
                    func.date(rentals_table.c.actual_end),
                    func.date(rentals_table.c.scheduled_end),
                ) >= date_from,
            ),
        )
        result = await self._session.execute(stmt)
        days_rented = max(result.scalar_one() or 0, 0)
        return (Decimal(days_rented * 100) / Decimal(days_in_period)).quantize(Decimal("0.01"))
