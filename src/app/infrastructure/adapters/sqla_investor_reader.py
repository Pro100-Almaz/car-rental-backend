from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.investor import InvestorQm
from app.core.queries.models.investor_payout import InvestorPayoutQm
from app.core.queries.models.vehicle_investor import VehicleInvestorQm
from app.core.queries.ports.investor_reader import (
    InvestorReader,
    ListInvestorPayoutsQm,
    ListInvestorsQm,
    ListVehicleInvestorsQm,
)
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.investor import investors_table
from app.infrastructure.persistence_sqla.mappings.investor_payout import investor_payouts_table
from app.infrastructure.persistence_sqla.mappings.vehicle_investor import vehicle_investors_table


class SqlaInvestorReader(InvestorReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _investor_columns(self) -> tuple[Any, ...]:
        return (
            investors_table.c.id,
            investors_table.c.organization_id,
            investors_table.c.full_name,
            investors_table.c.type.label("type_"),
            investors_table.c.contact_phone,
            investors_table.c.contact_email,
            investors_table.c.user_id,
            investors_table.c.notes,
            investors_table.c.created_at,
            investors_table.c.updated_at,
        )

    def _row_to_investor_qm(self, row: Row[Any]) -> InvestorQm:
        return InvestorQm(
            id=row.id,
            organization_id=row.organization_id,
            full_name=row.full_name,
            type_=row.type_,
            contact_phone=row.contact_phone,
            contact_email=row.contact_email,
            user_id=row.user_id,
            notes=row.notes,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _vehicle_investor_columns(self) -> tuple[Any, ...]:
        return (
            vehicle_investors_table.c.id,
            vehicle_investors_table.c.vehicle_id,
            vehicle_investors_table.c.investor_id,
            vehicle_investors_table.c.share_percentage,
            vehicle_investors_table.c.profit_distribution_type,
            vehicle_investors_table.c.created_at,
        )

    def _row_to_vehicle_investor_qm(self, row: Row[Any]) -> VehicleInvestorQm:
        return VehicleInvestorQm(
            id=row.id,
            vehicle_id=row.vehicle_id,
            investor_id=row.investor_id,
            share_percentage=row.share_percentage,
            profit_distribution_type=row.profit_distribution_type,
            created_at=row.created_at,
        )

    def _payout_columns(self) -> tuple[Any, ...]:
        return (
            investor_payouts_table.c.id,
            investor_payouts_table.c.organization_id,
            investor_payouts_table.c.investor_id,
            investor_payouts_table.c.period_month,
            investor_payouts_table.c.calculated_profit,
            investor_payouts_table.c.share_amount,
            investor_payouts_table.c.status,
            investor_payouts_table.c.paid_at,
            investor_payouts_table.c.notes,
            investor_payouts_table.c.created_at,
        )

    def _row_to_payout_qm(self, row: Row[Any]) -> InvestorPayoutQm:
        return InvestorPayoutQm(
            id=row.id,
            organization_id=row.organization_id,
            investor_id=row.investor_id,
            period_month=row.period_month,
            calculated_profit=row.calculated_profit,
            share_amount=row.share_amount,
            status=row.status,
            paid_at=row.paid_at,
            notes=row.notes,
            created_at=row.created_at,
        )

    async def get_by_id(
        self,
        *,
        investor_id: UUID,
    ) -> InvestorQm | None:
        stmt = select(*self._investor_columns()).where(
            investors_table.c.id == investor_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_investor_qm(row)

    async def list_investors(
        self,
        *,
        organization_id: UUID,
        type_: str | None = None,
    ) -> ListInvestorsQm:
        stmt = (
            select(*self._investor_columns())
            .where(investors_table.c.organization_id == organization_id)
            .order_by(investors_table.c.created_at.desc())
        )
        if type_ is not None:
            stmt = stmt.where(investors_table.c.type == type_)
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        investors = [self._row_to_investor_qm(row) for row in rows]
        return ListInvestorsQm(
            investors=investors,
            total=len(investors),
        )

    async def list_vehicle_investors(
        self,
        *,
        investor_id: UUID,
    ) -> ListVehicleInvestorsQm:
        stmt = (
            select(*self._vehicle_investor_columns())
            .where(vehicle_investors_table.c.investor_id == investor_id)
            .order_by(vehicle_investors_table.c.created_at.desc())
        )
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        vehicle_investors = [self._row_to_vehicle_investor_qm(row) for row in rows]
        return ListVehicleInvestorsQm(
            vehicle_investors=vehicle_investors,
            total=len(vehicle_investors),
        )

    async def list_investor_payouts(
        self,
        *,
        investor_id: UUID,
        status: str | None = None,
    ) -> ListInvestorPayoutsQm:
        stmt = (
            select(*self._payout_columns())
            .where(investor_payouts_table.c.investor_id == investor_id)
            .order_by(investor_payouts_table.c.period_month.desc())
        )
        if status is not None:
            stmt = stmt.where(investor_payouts_table.c.status == status)
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        payouts = [self._row_to_payout_qm(row) for row in rows]
        return ListInvestorPayoutsQm(
            payouts=payouts,
            total=len(payouts),
        )
