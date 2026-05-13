from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.core.commands.exceptions import VehiclePricingNotFoundError
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.vehicle_pricing_tx_storage import VehiclePricingTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import VehiclePricingId

logger = logging.getLogger(__name__)

_UNSET = object()


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateVehiclePricingRequest:
    vehicle_pricing_id: UUID
    base_daily_rate: Decimal | object = _UNSET
    name: str | object = _UNSET
    multiplier: Decimal | object = _UNSET
    valid_from: date | object = _UNSET
    valid_to: date | object = _UNSET
    is_active: bool | object = _UNSET


class UpdateVehiclePricing:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        vehicle_pricing_tx_storage: VehiclePricingTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._vehicle_pricing_tx_storage = vehicle_pricing_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateVehiclePricingRequest) -> None:
        logger.info("Update vehicle pricing: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.update",
            ),
        )

        vehicle_pricing_id = VehiclePricingId(request.vehicle_pricing_id)
        vehicle_pricing = await self._vehicle_pricing_tx_storage.get_by_id(vehicle_pricing_id, for_update=True)
        if vehicle_pricing is None:
            raise VehiclePricingNotFoundError

        changed = False
        for attr in ("base_daily_rate", "name", "multiplier", "valid_from", "valid_to", "is_active"):
            val = getattr(request, attr)
            if val is not _UNSET and val != getattr(vehicle_pricing, attr):
                setattr(vehicle_pricing, attr, val)
                changed = True

        if changed:
            await self._transaction_manager.commit()

        logger.info("Update vehicle pricing: done.")
