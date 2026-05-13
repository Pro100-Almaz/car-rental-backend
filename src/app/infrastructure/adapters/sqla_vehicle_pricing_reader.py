from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.vehicle_pricing import VehiclePricingQm
from app.core.queries.ports.vehicle_pricing_reader import ListVehiclePricingQm, VehiclePricingReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.vehicle_pricing import vehicle_pricing_table


class SqlaVehiclePricingReader(VehiclePricingReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            vehicle_pricing_table.c.id,
            vehicle_pricing_table.c.vehicle_id,
            vehicle_pricing_table.c.base_daily_rate,
            vehicle_pricing_table.c.name,
            vehicle_pricing_table.c.multiplier,
            vehicle_pricing_table.c.valid_from,
            vehicle_pricing_table.c.valid_to,
            vehicle_pricing_table.c.is_active,
            vehicle_pricing_table.c.created_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> VehiclePricingQm:
        return VehiclePricingQm(
            id=row.id,
            vehicle_id=row.vehicle_id,
            base_daily_rate=row.base_daily_rate,
            name=row.name,
            multiplier=row.multiplier,
            valid_from=row.valid_from,
            valid_to=row.valid_to,
            is_active=row.is_active,
            created_at=row.created_at,
        )

    async def get_by_id(
        self,
        *,
        vehicle_pricing_id: UUID,
    ) -> VehiclePricingQm | None:
        stmt = select(*self._base_columns()).where(
            vehicle_pricing_table.c.id == vehicle_pricing_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)

    async def list_vehicle_pricing(
        self,
        *,
        vehicle_id: UUID,
        is_active: bool | None = None,
    ) -> ListVehiclePricingQm:
        stmt = (
            select(*self._base_columns())
            .where(vehicle_pricing_table.c.vehicle_id == vehicle_id)
            .order_by(vehicle_pricing_table.c.valid_from.desc())
        )
        if is_active is not None:
            stmt = stmt.where(vehicle_pricing_table.c.is_active == is_active)
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        items = [self._row_to_qm(row) for row in rows]
        return ListVehiclePricingQm(items=items)
