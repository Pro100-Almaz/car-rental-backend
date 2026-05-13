from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.commands.exceptions import VehicleNotFoundError
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.ports.vehicle_tx_storage import VehicleTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import BranchId, FuelType, Transmission, VehicleId
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

_UNSET = object()


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateVehicleRequest:
    vehicle_id: UUID
    nickname: str | None | object = _UNSET
    make: str | object = _UNSET
    model: str | object = _UNSET
    year: int | object = _UNSET
    vin: str | None | object = _UNSET
    license_plate: str | object = _UNSET
    color: str | object = _UNSET
    category: str | object = _UNSET
    fuel_type: FuelType | object = _UNSET
    transmission: Transmission | object = _UNSET
    current_mileage: int | object = _UNSET
    purchase_price: Decimal | None | object = _UNSET
    purchase_date: date | None | object = _UNSET
    insurance_expiry: date | None | object = _UNSET
    inspection_expiry: date | None | object = _UNSET
    gps_device_id: str | None | object = _UNSET
    branch_id: UUID | None | object = _UNSET
    photos: list[str] | None | object = _UNSET
    features: dict[str, Any] | None | object = _UNSET
    pricing_override: dict[str, Any] | None | object = _UNSET


class UpdateVehicle:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        vehicle_tx_storage: VehicleTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._vehicle_tx_storage = vehicle_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateVehicleRequest) -> None:
        logger.info("Update vehicle: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.update",
            ),
        )

        vehicle_id = VehicleId(request.vehicle_id)
        vehicle = await self._vehicle_tx_storage.get_by_id(vehicle_id, for_update=True)
        if vehicle is None:
            raise VehicleNotFoundError

        changed = False
        for attr in (
            "nickname",
            "make",
            "model",
            "year",
            "vin",
            "license_plate",
            "color",
            "category",
            "fuel_type",
            "transmission",
            "current_mileage",
            "purchase_price",
            "purchase_date",
            "insurance_expiry",
            "inspection_expiry",
            "gps_device_id",
            "photos",
            "features",
            "pricing_override",
        ):
            val = getattr(request, attr)
            if val is not _UNSET and val != getattr(vehicle, attr):
                setattr(vehicle, attr, val)
                changed = True

        branch_val = request.branch_id
        if branch_val is not _UNSET:
            new_branch_id = BranchId(branch_val) if branch_val is not None else None  # type: ignore[arg-type]
            if new_branch_id != vehicle.branch_id:
                vehicle.branch_id = new_branch_id
                changed = True

        if changed:
            vehicle.updated_at = UtcDatetime(self._utc_timer.now.value)
            await self._transaction_manager.commit()

        logger.info("Update vehicle: done.")
