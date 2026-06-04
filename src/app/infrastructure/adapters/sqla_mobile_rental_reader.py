from typing import Any
from uuid import UUID

from sqlalchemy import Row, and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.mobile_rental import MobileRentalQm
from app.core.queries.ports.mobile_rental_reader import ListMobileRentalsQm, MobileRentalReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.rental import rentals_table


class SqlaMobileRentalReader(MobileRentalReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            rentals_table.c.id,
            rentals_table.c.organization_id,
            rentals_table.c.vehicle_id,
            rentals_table.c.client_id,
            rentals_table.c.status,
            rentals_table.c.booking_type,
            rentals_table.c.booked_at,
            rentals_table.c.scheduled_start,
            rentals_table.c.scheduled_end,
            rentals_table.c.actual_start,
            rentals_table.c.actual_end,
            rentals_table.c.base_rate,
            rentals_table.c.rate_type,
            rentals_table.c.estimated_total,
            rentals_table.c.actual_total,
            rentals_table.c.discount_amount,
            rentals_table.c.deposit_type,
            rentals_table.c.deposit_amount,
            rentals_table.c.deposit_status,
            rentals_table.c.deposit_refund_amount,
            rentals_table.c.prepayment_amount,
            rentals_table.c.prepayment_status,
            rentals_table.c.source,
            rentals_table.c.pickup_notes,
            rentals_table.c.cancellation_reason,
            rentals_table.c.created_at,
            rentals_table.c.updated_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> MobileRentalQm:
        return MobileRentalQm(
            id=row.id,
            organization_id=row.organization_id,
            vehicle_id=row.vehicle_id,
            client_id=row.client_id,
            status=row.status,
            booking_type=row.booking_type,
            booked_at=row.booked_at,
            scheduled_start=row.scheduled_start,
            scheduled_end=row.scheduled_end,
            actual_start=row.actual_start,
            actual_end=row.actual_end,
            base_rate=row.base_rate,
            rate_type=row.rate_type,
            estimated_total=row.estimated_total,
            actual_total=row.actual_total,
            discount_amount=row.discount_amount,
            deposit_type=row.deposit_type,
            deposit_amount=row.deposit_amount,
            deposit_status=row.deposit_status,
            deposit_refund_amount=row.deposit_refund_amount,
            prepayment_amount=row.prepayment_amount,
            prepayment_status=row.prepayment_status,
            source=row.source,
            pickup_notes=row.pickup_notes,
            cancellation_reason=row.cancellation_reason,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(
        self,
        *,
        rental_id: UUID,
        client_id: UUID,
    ) -> MobileRentalQm | None:
        stmt = select(*self._base_columns()).where(
            and_(
                rentals_table.c.id == rental_id,
                rentals_table.c.client_id == client_id,
            )
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)

    async def list_by_client(
        self,
        *,
        client_id: UUID,
        status: str | None = None,
    ) -> ListMobileRentalsQm:
        stmt = (
            select(*self._base_columns())
            .where(rentals_table.c.client_id == client_id)
            .order_by(rentals_table.c.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(rentals_table.c.status == status)
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        rentals = [self._row_to_qm(row) for row in rows]
        return ListMobileRentalsQm(rentals=rentals, total=len(rentals))

    async def get_active_by_client(
        self,
        *,
        client_id: UUID,
    ) -> MobileRentalQm | None:
        stmt = (
            select(*self._base_columns())
            .where(
                and_(
                    rentals_table.c.client_id == client_id,
                    rentals_table.c.status.in_(["active", "confirmed"]),
                )
            )
            .order_by(rentals_table.c.scheduled_start.asc())
            .limit(1)
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)
