from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.vehicle_tx_storage import VehicleTxStorage
from app.core.common.entities.types_ import VehicleId
from app.core.common.entities.vehicle import Vehicle
from app.infrastructure.exceptions import StorageError


class SqlaVehicleTxStorage(VehicleTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, vehicle: Vehicle) -> None:
        try:
            self._session.add(vehicle)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        vehicle_id: VehicleId,
        *,
        for_update: bool = False,
    ) -> Vehicle | None:
        try:
            return await self._session.get(
                Vehicle,
                vehicle_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
