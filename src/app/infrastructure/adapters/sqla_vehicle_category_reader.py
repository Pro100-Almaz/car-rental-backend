from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.vehicle_category import ListVehicleCategoriesQm, VehicleCategoryQm
from app.core.queries.ports.vehicle_category_reader import VehicleCategoryReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.vehicle_category import vehicle_categories_table


class SqlaVehicleCategoryReader(VehicleCategoryReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            vehicle_categories_table.c.id,
            vehicle_categories_table.c.organization_id,
            vehicle_categories_table.c.name,
            vehicle_categories_table.c.sort_order,
            vehicle_categories_table.c.is_active,
            vehicle_categories_table.c.created_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> VehicleCategoryQm:
        return VehicleCategoryQm(
            id=row.id,
            organization_id=row.organization_id,
            name=row.name,
            sort_order=row.sort_order,
            is_active=row.is_active,
            created_at=row.created_at,
        )

    async def list_categories(
        self,
        *,
        organization_id: UUID,
    ) -> ListVehicleCategoriesQm:
        stmt = (
            select(*self._base_columns())
            .where(vehicle_categories_table.c.organization_id == organization_id)
            .order_by(vehicle_categories_table.c.sort_order.asc())
        )
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        categories = [self._row_to_qm(row) for row in rows]
        return ListVehicleCategoriesQm(categories=categories, total=len(categories))
