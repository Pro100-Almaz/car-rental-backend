from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.additional_service import AdditionalServiceQm
from app.core.queries.ports.additional_service_reader import AdditionalServiceReader, ListAdditionalServicesQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.additional_service import additional_services_table


class SqlaAdditionalServiceReader(AdditionalServiceReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            additional_services_table.c.id,
            additional_services_table.c.organization_id,
            additional_services_table.c.name,
            additional_services_table.c.price,
            additional_services_table.c.is_active,
            additional_services_table.c.created_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> AdditionalServiceQm:
        return AdditionalServiceQm(
            id=row.id,
            organization_id=row.organization_id,
            name=row.name,
            price=row.price,
            is_active=row.is_active,
            created_at=row.created_at,
        )

    async def get_by_id(
        self,
        *,
        additional_service_id: UUID,
    ) -> AdditionalServiceQm | None:
        stmt = select(*self._base_columns()).where(
            additional_services_table.c.id == additional_service_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)

    async def list_additional_services(
        self,
        *,
        organization_id: UUID,
        is_active: bool | None = None,
    ) -> ListAdditionalServicesQm:
        stmt = (
            select(*self._base_columns())
            .where(additional_services_table.c.organization_id == organization_id)
            .order_by(additional_services_table.c.name)
        )
        if is_active is not None:
            stmt = stmt.where(additional_services_table.c.is_active == is_active)
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        additional_services = [self._row_to_qm(row) for row in rows]
        return ListAdditionalServicesQm(
            additional_services=additional_services,
            total=len(additional_services),
        )
