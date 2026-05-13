from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.vehicle_pricing_tx_storage import VehiclePricingTxStorage
from app.core.common.entities.types_ import VehiclePricingId
from app.core.common.entities.vehicle_pricing import VehiclePricing
from app.infrastructure.exceptions import StorageError


class SqlaVehiclePricingTxStorage(VehiclePricingTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, vehicle_pricing: VehiclePricing) -> None:
        try:
            self._session.add(vehicle_pricing)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        vehicle_pricing_id: VehiclePricingId,
        *,
        for_update: bool = False,
    ) -> VehiclePricing | None:
        try:
            return await self._session.get(
                VehiclePricing,
                vehicle_pricing_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
