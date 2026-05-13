from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.rental_service_tx_storage import RentalServiceTxStorage
from app.core.common.entities.rental_service import RentalService
from app.core.common.entities.types_ import RentalServiceId
from app.infrastructure.exceptions import StorageError


class SqlaRentalServiceTxStorage(RentalServiceTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, rental_service: RentalService) -> None:
        try:
            self._session.add(rental_service)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        rental_service_id: RentalServiceId,
        *,
        for_update: bool = False,
    ) -> RentalService | None:
        try:
            return await self._session.get(
                RentalService,
                rental_service_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e

    async def delete(self, rental_service: RentalService) -> None:
        try:
            await self._session.delete(rental_service)
        except SQLAlchemyError as e:
            raise StorageError from e
