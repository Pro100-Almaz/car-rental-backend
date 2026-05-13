from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.vehicle_investor_tx_storage import VehicleInvestorTxStorage
from app.core.common.entities.types_ import VehicleInvestorId
from app.core.common.entities.vehicle_investor import VehicleInvestor
from app.infrastructure.exceptions import StorageError


class SqlaVehicleInvestorTxStorage(VehicleInvestorTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, vehicle_investor: VehicleInvestor) -> None:
        try:
            self._session.add(vehicle_investor)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        vehicle_investor_id: VehicleInvestorId,
        *,
        for_update: bool = False,
    ) -> VehicleInvestor | None:
        try:
            return await self._session.get(
                VehicleInvestor,
                vehicle_investor_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e

    async def delete(self, vehicle_investor: VehicleInvestor) -> None:
        try:
            await self._session.delete(vehicle_investor)
        except SQLAlchemyError as e:
            raise StorageError from e
