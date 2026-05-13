import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.ports.vehicle_pricing_tx_storage import VehiclePricingTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import VehicleId
from app.core.common.entities.vehicle_pricing import VehiclePricing
from app.core.common.factories.id_factory import create_vehicle_pricing_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateVehiclePricingRequest:
    vehicle_id: UUID
    base_daily_rate: Decimal
    name: str
    multiplier: Decimal = Decimal("1.0")
    valid_from: date
    valid_to: date
    is_active: bool = True


class CreateVehiclePricingResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateVehiclePricing:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        vehicle_pricing_tx_storage: VehiclePricingTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._vehicle_pricing_tx_storage = vehicle_pricing_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateVehiclePricingRequest) -> CreateVehiclePricingResponse:
        logger.info("Create vehicle pricing: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        vehicle_pricing = VehiclePricing(
            id_=create_vehicle_pricing_id(),
            vehicle_id=VehicleId(request.vehicle_id),
            base_daily_rate=request.base_daily_rate,
            name=request.name,
            multiplier=request.multiplier,
            valid_from=request.valid_from,
            valid_to=request.valid_to,
            is_active=request.is_active,
            created_at=now,
        )
        self._vehicle_pricing_tx_storage.add(vehicle_pricing)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create vehicle pricing: done.")
        return CreateVehiclePricingResponse(
            id=vehicle_pricing.id_,
            created_at=vehicle_pricing.created_at.value,
        )
