from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, TypedDict
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.ports.vehicle_tx_storage import VehicleTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import (
    BranchId,
    FuelType,
    OrganizationId,
    Transmission,
    VehicleCategory,
    VehicleStatus,
)
from app.core.common.entities.vehicle import Vehicle
from app.core.common.factories.id_factory import create_vehicle_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateVehicleRequest:
    organization_id: UUID
    nickname: str | None = None
    make: str
    model: str
    year: int
    vin: str | None = None
    license_plate: str
    color: str
    category: VehicleCategory
    fuel_type: FuelType
    transmission: Transmission
    current_mileage: int = 0
    purchase_price: Decimal | None = None
    purchase_date: date | None = None
    insurance_expiry: date | None = None
    inspection_expiry: date | None = None
    gps_device_id: str | None = None
    branch_id: UUID | None = None
    photos: list[str] | None = None
    features: dict[str, Any] | None = None
    pricing_override: dict[str, Any] | None = None


class CreateVehicleResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateVehicle:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        vehicle_tx_storage: VehicleTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._vehicle_tx_storage = vehicle_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateVehicleRequest) -> CreateVehicleResponse:
        logger.info("Create vehicle: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        vehicle = Vehicle(
            id_=create_vehicle_id(),
            organization_id=OrganizationId(request.organization_id),
            nickname=request.nickname,
            make=request.make,
            model=request.model,
            year=request.year,
            vin=request.vin,
            license_plate=request.license_plate,
            color=request.color,
            category=request.category,
            status=VehicleStatus.AVAILABLE,
            fuel_type=request.fuel_type,
            transmission=request.transmission,
            current_mileage=request.current_mileage,
            purchase_price=request.purchase_price,
            purchase_date=request.purchase_date,
            insurance_expiry=request.insurance_expiry,
            inspection_expiry=request.inspection_expiry,
            gps_device_id=request.gps_device_id,
            current_latitude=None,
            current_longitude=None,
            current_fuel_level=None,
            branch_id=BranchId(request.branch_id) if request.branch_id else None,
            photos=request.photos,
            features=request.features,
            pricing_override=request.pricing_override,
            created_at=now,
            updated_at=now,
        )
        self._vehicle_tx_storage.add(vehicle)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create vehicle: done.")
        return CreateVehicleResponse(
            id=vehicle.id_,
            created_at=vehicle.created_at.value,
        )
