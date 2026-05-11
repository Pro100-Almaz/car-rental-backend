from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.common.entities.rental import Rental
from app.core.common.entities.types_ import RentalId
from app.infrastructure.exceptions import StorageError


class SqlaRentalTxStorage(RentalTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, rental: Rental) -> None:
        try:
            self._session.add(rental)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        rental_id: RentalId,
        *,
        for_update: bool = False,
    ) -> Rental | None:
        try:
            return await self._session.get(
                Rental,
                rental_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
