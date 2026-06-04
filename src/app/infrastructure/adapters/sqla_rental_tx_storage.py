from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.common.entities.rental import Rental
from app.core.common.entities.types_ import RentalId, VehicleId
from app.infrastructure.exceptions import StorageError
from app.infrastructure.persistence_sqla.mappings.rental import rentals_table


class SqlaRentalTxStorage(RentalTxStorage):
    _NON_BLOCKING_STATUSES = ("cancelled", "completed")

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

    async def has_overlap(
        self,
        vehicle_id: VehicleId,
        scheduled_start: datetime,
        scheduled_end: datetime,
    ) -> bool:
        stmt = (
            select(rentals_table.c.id)
            .where(
                rentals_table.c.vehicle_id == vehicle_id,
                rentals_table.c.status.notin_(self._NON_BLOCKING_STATUSES),
                rentals_table.c.scheduled_start < scheduled_end,
                rentals_table.c.scheduled_end > scheduled_start,
            )
            .limit(1)
        )
        try:
            result = await self._session.execute(stmt)
            return result.first() is not None
        except SQLAlchemyError as e:
            raise StorageError from e
