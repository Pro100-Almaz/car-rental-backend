from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.vehicle_category_tx_storage import VehicleCategoryTxStorage
from app.core.common.entities.vehicle_category import VehicleCategoryEntity
from app.infrastructure.exceptions import StorageError


class SqlaVehicleCategoryTxStorage(VehicleCategoryTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, category: VehicleCategoryEntity) -> None:
        self._session.add(category)

    async def get_by_id(self, category_id: UUID) -> VehicleCategoryEntity | None:
        try:
            return await self._session.get(VehicleCategoryEntity, category_id)
        except SQLAlchemyError as e:
            raise StorageError from e
