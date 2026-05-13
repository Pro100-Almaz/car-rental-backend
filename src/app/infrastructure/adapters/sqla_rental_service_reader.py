from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.rental_service import RentalServiceQm
from app.core.queries.ports.rental_service_reader import ListRentalServicesQm, RentalServiceReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.rental_service import rental_services_table


class SqlaRentalServiceReader(RentalServiceReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            rental_services_table.c.id,
            rental_services_table.c.rental_id,
            rental_services_table.c.service_id,
            rental_services_table.c.quantity,
            rental_services_table.c.price,
        )

    def _row_to_qm(self, row: Row[Any]) -> RentalServiceQm:
        return RentalServiceQm(
            id=row.id,
            rental_id=row.rental_id,
            service_id=row.service_id,
            quantity=row.quantity,
            price=row.price,
        )

    async def list_rental_services(
        self,
        *,
        rental_id: UUID,
    ) -> ListRentalServicesQm:
        stmt = select(*self._base_columns()).where(
            rental_services_table.c.rental_id == rental_id,
        )
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        rental_services = [self._row_to_qm(row) for row in rows]
        return ListRentalServicesQm(
            rental_services=rental_services,
            total=len(rental_services),
        )
