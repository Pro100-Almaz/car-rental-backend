from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.dashboard_active_rentals import (
    ActiveRentalItemQm,
    DashboardActiveRentalsQm,
    ReturnTodayItemQm,
)
from app.core.queries.models.dashboard_alerts import (
    ClientDebtAlertQm,
    DashboardAlertsQm,
    ExpiringDocumentAlertQm,
    OverdueReturnAlertQm,
)
from app.core.queries.models.dashboard_kpis import (
    DashboardKpisQm,
    FleetStatusQm,
    KpiValueQm,
)
from app.core.queries.models.dashboard_revenue_chart import (
    DashboardRevenueChartQm,
    RevenueDataPointQm,
)
from app.core.queries.ports.dashboard_reader import DashboardReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.cash_journal_entry import cash_journal_table
from app.infrastructure.persistence_sqla.mappings.client import clients_table
from app.infrastructure.persistence_sqla.mappings.rental import rentals_table
from app.infrastructure.persistence_sqla.mappings.vehicle import vehicles_table


class SqlaDashboardReader(DashboardReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_kpis(
        self,
        *,
        organization_id: UUID,
        date_from: date,
        date_to: date,
        prev_date_from: date,
        prev_date_to: date,
        now: datetime,
    ) -> DashboardKpisQm:
        try:
            cur_revenue = await self._sum_journal(organization_id, date_from, date_to, "income")
            cur_expenses = await self._sum_journal(organization_id, date_from, date_to, "expense")
            prev_revenue = await self._sum_journal(organization_id, prev_date_from, prev_date_to, "income")
            prev_expenses = await self._sum_journal(organization_id, prev_date_from, prev_date_to, "expense")

            cur_net = cur_revenue - cur_expenses
            prev_net = prev_revenue - prev_expenses

            fleet_status = await self._get_fleet_status(organization_id)
            active_vehicles = fleet_status.total - fleet_status.other
            cur_util = Decimal(fleet_status.rented * 100) / Decimal(max(active_vehicles, 1))
            prev_util = cur_util

            cur_active = await self._count_active_rentals(organization_id)
            prev_active = cur_active

            cur_debts = await self._sum_debts(organization_id)
            prev_debts = cur_debts
        except SQLAlchemyError as e:
            raise ReaderError from e

        return DashboardKpisQm(
            period_from=date_from.isoformat(),
            period_to=date_to.isoformat(),
            total_revenue=self._make_kpi(cur_revenue, prev_revenue),
            total_expenses=self._make_kpi(cur_expenses, prev_expenses),
            net_profit=self._make_kpi(cur_net, prev_net),
            fleet_utilization=self._make_kpi(cur_util.quantize(Decimal("0.01")), prev_util.quantize(Decimal("0.01"))),
            active_rentals_count=self._make_kpi(cur_active, prev_active),
            outstanding_debts=self._make_kpi(cur_debts, prev_debts),
            fleet_status=fleet_status,
        )

    async def get_alerts(
        self,
        *,
        organization_id: UUID,
        now: datetime,
    ) -> DashboardAlertsQm:
        try:
            overdue = await self._get_overdue_returns(organization_id, now)
            expiring = await self._get_expiring_documents(organization_id, now.date())
            debtors = await self._get_clients_with_debt(organization_id)
        except SQLAlchemyError as e:
            raise ReaderError from e

        total = len(overdue) + len(expiring) + len(debtors)
        return DashboardAlertsQm(
            overdue_returns=overdue,
            expiring_documents=expiring,
            clients_with_debt=debtors,
            total_alerts=total,
        )

    async def get_active_rentals(
        self,
        *,
        organization_id: UUID,
        limit: int,
        now: datetime,
    ) -> DashboardActiveRentalsQm:
        try:
            active = await self._get_top_active_rentals(organization_id, limit, now)
            returns_today = await self._get_returns_today(organization_id, now)
        except SQLAlchemyError as e:
            raise ReaderError from e

        return DashboardActiveRentalsQm(
            active_rentals=active,
            returns_today_count=len(returns_today),
            returns_today=returns_today,
        )

    async def get_revenue_chart(
        self,
        *,
        organization_id: UUID,
        date_from: date,
        date_to: date,
    ) -> DashboardRevenueChartQm:
        try:
            stmt = (
                select(
                    cash_journal_table.c.date.label("day"),
                    func.coalesce(func.sum(cash_journal_table.c.amount), Decimal(0)).label("revenue"),
                )
                .where(
                    and_(
                        cash_journal_table.c.organization_id == organization_id,
                        cash_journal_table.c.operation_type == "income",
                        cash_journal_table.c.date >= date_from,
                        cash_journal_table.c.date <= date_to,
                    ),
                )
                .group_by(cash_journal_table.c.date)
                .order_by(cash_journal_table.c.date)
            )
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e

        data_points = [
            RevenueDataPointQm(date=row.day.isoformat(), revenue=row.revenue)
            for row in rows
        ]
        total = sum(dp.revenue for dp in data_points)

        return DashboardRevenueChartQm(
            period_from=date_from.isoformat(),
            period_to=date_to.isoformat(),
            data_points=data_points,
            total=total,
        )

    # --- private helpers ---

    async def _sum_journal(
        self, organization_id: UUID, d_from: date, d_to: date, op_type: str,
    ) -> Decimal:
        stmt = select(
            func.coalesce(func.sum(cash_journal_table.c.amount), Decimal(0)),
        ).where(
            and_(
                cash_journal_table.c.organization_id == organization_id,
                cash_journal_table.c.operation_type == op_type,
                cash_journal_table.c.date >= d_from,
                cash_journal_table.c.date <= d_to,
            ),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or Decimal(0)

    async def _get_fleet_status(self, organization_id: UUID) -> FleetStatusQm:
        stmt = select(
            vehicles_table.c.status,
            func.count().label("cnt"),
        ).where(
            vehicles_table.c.organization_id == organization_id,
        ).group_by(vehicles_table.c.status)
        result = await self._session.execute(stmt)

        counts: dict[str, int] = {}
        for row in result.all():
            counts[row.status] = row.cnt

        available = counts.get("available", 0)
        rented = counts.get("rented", 0) + counts.get("returning", 0)
        reserved = counts.get("reserved", 0)
        in_service = counts.get("in_service", 0) + counts.get("in_wash", 0)
        decommissioned = counts.get("decommissioned", 0) + counts.get("sold", 0)
        total = sum(counts.values())

        return FleetStatusQm(
            available=available,
            rented=rented,
            reserved=reserved,
            in_service=in_service,
            other=decommissioned,
            total=total,
        )

    async def _count_active_rentals(self, organization_id: UUID) -> int:
        stmt = select(func.count()).select_from(rentals_table).where(
            and_(
                rentals_table.c.organization_id == organization_id,
                rentals_table.c.status == "active",
            ),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def _sum_debts(self, organization_id: UUID) -> Decimal:
        stmt = select(
            func.coalesce(func.sum(clients_table.c.debt_balance), Decimal(0)),
        ).where(
            and_(
                clients_table.c.organization_id == organization_id,
                clients_table.c.debt_balance > 0,
            ),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or Decimal(0)

    async def _get_overdue_returns(
        self, organization_id: UUID, now: datetime,
    ) -> list[OverdueReturnAlertQm]:
        stmt = (
            select(
                rentals_table.c.id.label("rental_id"),
                vehicles_table.c.nickname.label("vehicle_nickname"),
                vehicles_table.c.license_plate,
                func.concat(clients_table.c.first_name, " ", clients_table.c.last_name).label("client_name"),
                rentals_table.c.scheduled_end,
            )
            .select_from(
                rentals_table
                .join(vehicles_table, rentals_table.c.vehicle_id == vehicles_table.c.id)
                .join(clients_table, rentals_table.c.client_id == clients_table.c.id)
            )
            .where(
                and_(
                    rentals_table.c.organization_id == organization_id,
                    rentals_table.c.status == "active",
                    rentals_table.c.scheduled_end < now,
                ),
            )
            .order_by(rentals_table.c.scheduled_end.asc())
        )
        result = await self._session.execute(stmt)
        return [
            OverdueReturnAlertQm(
                rental_id=row.rental_id,
                vehicle_nickname=row.vehicle_nickname,
                license_plate=row.license_plate,
                client_name=row.client_name,
                scheduled_end=row.scheduled_end,
                days_overdue=(now - row.scheduled_end).days,
            )
            for row in result.all()
        ]

    async def _get_expiring_documents(
        self, organization_id: UUID, today: date,
    ) -> list[ExpiringDocumentAlertQm]:
        threshold = today + timedelta(days=30)
        alerts: list[ExpiringDocumentAlertQm] = []

        for col, doc_type in [
            (vehicles_table.c.insurance_expiry, "insurance"),
            (vehicles_table.c.inspection_expiry, "inspection"),
        ]:
            stmt = (
                select(
                    vehicles_table.c.id,
                    vehicles_table.c.nickname,
                    vehicles_table.c.license_plate,
                    col.label("expiry_date"),
                )
                .where(
                    and_(
                        vehicles_table.c.organization_id == organization_id,
                        vehicles_table.c.status.notin_(["decommissioned", "sold"]),
                        col.isnot(None),
                        col <= threshold,
                    ),
                )
                .order_by(col.asc())
            )
            result = await self._session.execute(stmt)
            for row in result.all():
                alerts.append(
                    ExpiringDocumentAlertQm(
                        vehicle_id=row.id,
                        vehicle_nickname=row.nickname,
                        license_plate=row.license_plate,
                        document_type=doc_type,
                        expiry_date=row.expiry_date,
                        days_remaining=(row.expiry_date - today).days,
                    )
                )

        alerts.sort(key=lambda a: a.days_remaining)
        return alerts

    async def _get_clients_with_debt(
        self, organization_id: UUID,
    ) -> list[ClientDebtAlertQm]:
        stmt = (
            select(
                clients_table.c.id,
                func.concat(clients_table.c.first_name, " ", clients_table.c.last_name).label("client_name"),
                clients_table.c.phone,
                clients_table.c.debt_balance,
            )
            .where(
                and_(
                    clients_table.c.organization_id == organization_id,
                    clients_table.c.debt_balance > 0,
                ),
            )
            .order_by(clients_table.c.debt_balance.desc())
        )
        result = await self._session.execute(stmt)
        return [
            ClientDebtAlertQm(
                client_id=row.id,
                client_name=row.client_name,
                phone=row.phone,
                debt_balance=str(row.debt_balance),
            )
            for row in result.all()
        ]

    async def _get_top_active_rentals(
        self, organization_id: UUID, limit: int, now: datetime,
    ) -> list[ActiveRentalItemQm]:
        stmt = (
            select(
                rentals_table.c.id.label("rental_id"),
                rentals_table.c.vehicle_id,
                vehicles_table.c.nickname.label("vehicle_nickname"),
                vehicles_table.c.license_plate,
                rentals_table.c.client_id,
                func.concat(clients_table.c.first_name, " ", clients_table.c.last_name).label("client_name"),
                rentals_table.c.scheduled_end,
            )
            .select_from(
                rentals_table
                .join(vehicles_table, rentals_table.c.vehicle_id == vehicles_table.c.id)
                .join(clients_table, rentals_table.c.client_id == clients_table.c.id)
            )
            .where(
                and_(
                    rentals_table.c.organization_id == organization_id,
                    rentals_table.c.status == "active",
                ),
            )
            .order_by(rentals_table.c.scheduled_end.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [
            ActiveRentalItemQm(
                rental_id=row.rental_id,
                vehicle_id=row.vehicle_id,
                vehicle_nickname=row.vehicle_nickname,
                license_plate=row.license_plate,
                client_id=row.client_id,
                client_name=row.client_name,
                scheduled_end=row.scheduled_end,
                hours_remaining=max(int((row.scheduled_end - now).total_seconds() // 3600), 0),
            )
            for row in result.all()
        ]

    async def _get_returns_today(
        self, organization_id: UUID, now: datetime,
    ) -> list[ReturnTodayItemQm]:
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        stmt = (
            select(
                rentals_table.c.id.label("rental_id"),
                rentals_table.c.vehicle_id,
                vehicles_table.c.nickname.label("vehicle_nickname"),
                vehicles_table.c.license_plate,
                func.concat(clients_table.c.first_name, " ", clients_table.c.last_name).label("client_name"),
                rentals_table.c.scheduled_end,
            )
            .select_from(
                rentals_table
                .join(vehicles_table, rentals_table.c.vehicle_id == vehicles_table.c.id)
                .join(clients_table, rentals_table.c.client_id == clients_table.c.id)
            )
            .where(
                and_(
                    rentals_table.c.organization_id == organization_id,
                    rentals_table.c.status == "active",
                    rentals_table.c.scheduled_end >= today_start,
                    rentals_table.c.scheduled_end <= today_end,
                ),
            )
            .order_by(rentals_table.c.scheduled_end.asc())
        )
        result = await self._session.execute(stmt)
        return [
            ReturnTodayItemQm(
                rental_id=row.rental_id,
                vehicle_id=row.vehicle_id,
                vehicle_nickname=row.vehicle_nickname,
                license_plate=row.license_plate,
                client_name=row.client_name,
                scheduled_end=row.scheduled_end,
            )
            for row in result.all()
        ]

    @staticmethod
    def _make_kpi(current: Decimal | int, previous: Decimal | int) -> KpiValueQm:
        if previous and previous != 0:
            change = ((Decimal(str(current)) - Decimal(str(previous))) / Decimal(str(abs(previous)))) * 100
            change = change.quantize(Decimal("0.01"))
        else:
            change = None
        return KpiValueQm(value=current, previous_value=previous, change_percent=change)
