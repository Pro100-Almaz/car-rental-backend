from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Row, and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.mobile_vehicle import MobileVehicleQm
from app.core.queries.ports.mobile_vehicle_reader import (
    ListMobileVehiclesQm,
    MobileVehicleReader,
    VehicleAvailabilityQm,
)
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.rental import rentals_table
from app.infrastructure.persistence_sqla.mappings.vehicle import vehicles_table


class SqlaMobileVehicleReader(MobileVehicleReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            vehicles_table.c.id,
            vehicles_table.c.organization_id,
            vehicles_table.c.nickname,
            vehicles_table.c.make,
            vehicles_table.c.model,
            vehicles_table.c.year,
            vehicles_table.c.license_plate,
            vehicles_table.c.color,
            vehicles_table.c.category,
            vehicles_table.c.status,
            vehicles_table.c.fuel_type,
            vehicles_table.c.transmission,
            vehicles_table.c.branch_id,
            vehicles_table.c.photos,
            vehicles_table.c.features,
            vehicles_table.c.created_at,
            vehicles_table.c.updated_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> MobileVehicleQm:
        return MobileVehicleQm(
            id=row.id,
            organization_id=row.organization_id,
            nickname=row.nickname,
            make=row.make,
            model=row.model,
            year=row.year,
            license_plate=row.license_plate,
            color=row.color,
            category=row.category,
            status=row.status,
            fuel_type=row.fuel_type,
            transmission=row.transmission,
            branch_id=row.branch_id,
            photos=row.photos,
            features=row.features,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(
        self,
        *,
        vehicle_id: UUID,
        organization_id: UUID,
    ) -> MobileVehicleQm | None:
        stmt = select(*self._base_columns()).where(
            and_(
                vehicles_table.c.id == vehicle_id,
                vehicles_table.c.organization_id == organization_id,
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

    async def list_available(
        self,
        *,
        organization_id: UUID,
        category: str | None = None,
        fuel_type: str | None = None,
        transmission: str | None = None,
        branch_id: UUID | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> ListMobileVehiclesQm:
        stmt = (
            select(*self._base_columns())
            .where(
                and_(
                    vehicles_table.c.organization_id == organization_id,
                    vehicles_table.c.status == "available",
                )
            )
            .order_by(vehicles_table.c.make, vehicles_table.c.model)
        )
        if category is not None:
            stmt = stmt.where(vehicles_table.c.category == category)
        if fuel_type is not None:
            stmt = stmt.where(vehicles_table.c.fuel_type == fuel_type)
        if transmission is not None:
            stmt = stmt.where(vehicles_table.c.transmission == transmission)
        if branch_id is not None:
            stmt = stmt.where(vehicles_table.c.branch_id == branch_id)
        if search is not None:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    vehicles_table.c.nickname.ilike(pattern),
                    vehicles_table.c.license_plate.ilike(pattern),
                    vehicles_table.c.make.ilike(pattern),
                    vehicles_table.c.model.ilike(pattern),
                )
            )
        if date_from is not None and date_to is not None:
            booked_vehicle_ids = (
                select(rentals_table.c.vehicle_id)
                .where(
                    and_(
                        rentals_table.c.status.in_(["pending", "confirmed", "active"]),
                        rentals_table.c.scheduled_start < date_to,
                        rentals_table.c.scheduled_end > date_from,
                    )
                )
                .scalar_subquery()
            )
            stmt = stmt.where(vehicles_table.c.id.notin_(booked_vehicle_ids))
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        vehicles = [self._row_to_qm(row) for row in rows]
        return ListMobileVehiclesQm(vehicles=vehicles, total=len(vehicles))

    async def check_availability(
        self,
        *,
        vehicle_id: UUID,
        scheduled_start: datetime,
        scheduled_end: datetime,
    ) -> VehicleAvailabilityQm:
        stmt = select(
            rentals_table.c.scheduled_start,
            rentals_table.c.scheduled_end,
        ).where(
            and_(
                rentals_table.c.vehicle_id == vehicle_id,
                rentals_table.c.status.in_(["pending", "confirmed", "active"]),
                rentals_table.c.scheduled_start < scheduled_end,
                rentals_table.c.scheduled_end > scheduled_start,
            )
        )
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        conflicts = [
            {"start": row.scheduled_start, "end": row.scheduled_end}
            for row in rows
        ]
        return VehicleAvailabilityQm(
            vehicle_id=vehicle_id,
            is_available=len(conflicts) == 0,
            conflicting_periods=conflicts,
        )
