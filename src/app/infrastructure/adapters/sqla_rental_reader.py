from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.rental import RentalQm
from app.core.queries.ports.rental_reader import ListRentalsQm, RentalReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.rental import rentals_table


class SqlaRentalReader(RentalReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            rentals_table.c.id,
            rentals_table.c.organization_id,
            rentals_table.c.vehicle_id,
            rentals_table.c.client_id,
            rentals_table.c.manager_id,
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
            rentals_table.c.discount_code,
            rentals_table.c.discount_amount,
            rentals_table.c.late_fee,
            rentals_table.c.mileage_surcharge,
            rentals_table.c.fuel_charge,
            rentals_table.c.wash_fee,
            rentals_table.c.damage_charge,
            rentals_table.c.fine_charge,
            rentals_table.c.deposit_type,
            rentals_table.c.deposit_amount,
            rentals_table.c.deposit_status,
            rentals_table.c.deposit_refund_amount,
            rentals_table.c.checkin_data,
            rentals_table.c.checkout_data,
            rentals_table.c.invoice_url,
            rentals_table.c.cancellation_reason,
            rentals_table.c.prepayment_amount,
            rentals_table.c.prepayment_status,
            rentals_table.c.notes,
            rentals_table.c.created_at,
            rentals_table.c.updated_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> RentalQm:
        return RentalQm(
            id=row.id,
            organization_id=row.organization_id,
            vehicle_id=row.vehicle_id,
            client_id=row.client_id,
            manager_id=row.manager_id,
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
            discount_code=row.discount_code,
            discount_amount=row.discount_amount,
            late_fee=row.late_fee,
            mileage_surcharge=row.mileage_surcharge,
            fuel_charge=row.fuel_charge,
            wash_fee=row.wash_fee,
            damage_charge=row.damage_charge,
            fine_charge=row.fine_charge,
            deposit_type=row.deposit_type,
            deposit_amount=row.deposit_amount,
            deposit_status=row.deposit_status,
            deposit_refund_amount=row.deposit_refund_amount,
            checkin_data=row.checkin_data,
            checkout_data=row.checkout_data,
            invoice_url=row.invoice_url,
            cancellation_reason=row.cancellation_reason,
            prepayment_amount=row.prepayment_amount,
            prepayment_status=row.prepayment_status,
            notes=row.notes,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(
        self,
        *,
        rental_id: UUID,
    ) -> RentalQm | None:
        stmt = select(*self._base_columns()).where(
            rentals_table.c.id == rental_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)

    async def list_rentals(
        self,
        *,
        organization_id: UUID,
        status: str | None = None,
        vehicle_id: UUID | None = None,
        client_id: UUID | None = None,
    ) -> ListRentalsQm:
        stmt = (
            select(*self._base_columns())
            .where(rentals_table.c.organization_id == organization_id)
            .order_by(rentals_table.c.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(rentals_table.c.status == status)
        if vehicle_id is not None:
            stmt = stmt.where(rentals_table.c.vehicle_id == vehicle_id)
        if client_id is not None:
            stmt = stmt.where(rentals_table.c.client_id == client_id)
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        rentals = [self._row_to_qm(row) for row in rows]
        return ListRentalsQm(
            rentals=rentals,
            total=len(rentals),
        )
