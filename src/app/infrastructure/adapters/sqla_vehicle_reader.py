from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.vehicle import VehicleQm
from app.core.queries.ports.vehicle_reader import ListVehiclesQm, VehicleReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.vehicle import vehicles_table


class SqlaVehicleReader(VehicleReader):
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
            vehicles_table.c.vin,
            vehicles_table.c.license_plate,
            vehicles_table.c.color,
            vehicles_table.c.category,
            vehicles_table.c.status,
            vehicles_table.c.fuel_type,
            vehicles_table.c.transmission,
            vehicles_table.c.current_mileage,
            vehicles_table.c.purchase_price,
            vehicles_table.c.purchase_date,
            vehicles_table.c.insurance_expiry,
            vehicles_table.c.inspection_expiry,
            vehicles_table.c.gps_device_id,
            vehicles_table.c.current_latitude,
            vehicles_table.c.current_longitude,
            vehicles_table.c.current_fuel_level,
            vehicles_table.c.branch_id,
            vehicles_table.c.photos,
            vehicles_table.c.features,
            vehicles_table.c.pricing_override,
            vehicles_table.c.created_at,
            vehicles_table.c.updated_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> VehicleQm:
        return VehicleQm(
            id=row.id,
            organization_id=row.organization_id,
            nickname=row.nickname,
            make=row.make,
            model=row.model,
            year=row.year,
            vin=row.vin,
            license_plate=row.license_plate,
            color=row.color,
            category=row.category,
            status=row.status,
            fuel_type=row.fuel_type,
            transmission=row.transmission,
            current_mileage=row.current_mileage,
            purchase_price=row.purchase_price,
            purchase_date=row.purchase_date,
            insurance_expiry=row.insurance_expiry,
            inspection_expiry=row.inspection_expiry,
            gps_device_id=row.gps_device_id,
            current_latitude=row.current_latitude,
            current_longitude=row.current_longitude,
            current_fuel_level=row.current_fuel_level,
            branch_id=row.branch_id,
            photos=row.photos,
            features=row.features,
            pricing_override=row.pricing_override,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(
        self,
        *,
        vehicle_id: UUID,
    ) -> VehicleQm | None:
        stmt = select(*self._base_columns()).where(
            vehicles_table.c.id == vehicle_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)

    async def list_vehicles(
        self,
        *,
        organization_id: UUID,
        status: str | None = None,
        branch_id: UUID | None = None,
    ) -> ListVehiclesQm:
        stmt = (
            select(*self._base_columns())
            .where(vehicles_table.c.organization_id == organization_id)
            .order_by(vehicles_table.c.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(vehicles_table.c.status == status)
        if branch_id is not None:
            stmt = stmt.where(vehicles_table.c.branch_id == branch_id)
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        vehicles = [self._row_to_qm(row) for row in rows]
        return ListVehiclesQm(
            vehicles=vehicles,
            total=len(vehicles),
        )
