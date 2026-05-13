from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.vehicle_financials import VehicleFinancialsQm
from app.core.queries.ports.vehicle_financials_reader import VehicleFinancialsReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.cash_journal_entry import cash_journal_table
from app.infrastructure.persistence_sqla.mappings.rental import rentals_table


class SqlaVehicleFinancialsReader(VehicleFinancialsReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_financials(
        self,
        *,
        vehicle_id: UUID,
        date_from: date,
        date_to: date,
    ) -> VehicleFinancialsQm:
        try:
            revenue_result = await self._get_revenue(vehicle_id, date_from, date_to)
            expense_result = await self._get_expenses(vehicle_id, date_from, date_to)
            rental_stats = await self._get_rental_stats(vehicle_id, date_from, date_to)
        except SQLAlchemyError as e:
            raise ReaderError from e

        total_revenue = revenue_result or Decimal(0)
        total_expenses = expense_result or Decimal(0)
        net_profit = total_revenue - total_expenses

        days_in_period = max((date_to - date_from).days, 1)
        days_rented = rental_stats["days_rented"]
        total_rentals = rental_stats["total_rentals"]
        utilization = Decimal(days_rented * 100) / Decimal(days_in_period)

        return VehicleFinancialsQm(
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            net_profit=net_profit,
            total_rentals=total_rentals,
            days_rented=days_rented,
            days_in_period=days_in_period,
            utilization_percent=utilization.quantize(Decimal("0.01")),
        )

    async def _get_revenue(
        self, vehicle_id: UUID, date_from: date, date_to: date,
    ) -> Decimal | None:
        stmt = select(
            func.coalesce(func.sum(rentals_table.c.actual_total), Decimal(0)),
        ).where(
            and_(
                rentals_table.c.vehicle_id == vehicle_id,
                rentals_table.c.status.in_(["completed", "returning"]),
                rentals_table.c.actual_start.isnot(None),
                func.date(rentals_table.c.actual_start) <= date_to,
                func.coalesce(
                    func.date(rentals_table.c.actual_end),
                    func.date(rentals_table.c.scheduled_end),
                ) >= date_from,
            ),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _get_expenses(
        self, vehicle_id: UUID, date_from: date, date_to: date,
    ) -> Decimal | None:
        stmt = select(
            func.coalesce(func.sum(cash_journal_table.c.amount), Decimal(0)),
        ).where(
            and_(
                cash_journal_table.c.vehicle_id == vehicle_id,
                cash_journal_table.c.operation_type == "expense",
                cash_journal_table.c.date >= date_from,
                cash_journal_table.c.date <= date_to,
            ),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _get_rental_stats(
        self, vehicle_id: UUID, date_from: date, date_to: date,
    ) -> dict:
        stmt = select(
            func.count().label("total_rentals"),
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
        row = result.one()
        return {
            "total_rentals": row.total_rentals,
            "days_rented": max(row.days_rented, 0),
        }
