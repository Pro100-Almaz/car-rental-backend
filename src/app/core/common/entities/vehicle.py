from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    BranchId,
    FuelType,
    OrganizationId,
    Transmission,
    VehicleCategory,
    VehicleId,
    VehicleStatus,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class Vehicle(Entity[VehicleId]):
    def __init__(
        self,
        *,
        id_: VehicleId,
        organization_id: OrganizationId,
        nickname: str | None,
        make: str,
        model: str,
        year: int,
        vin: str | None,
        license_plate: str,
        color: str,
        category: VehicleCategory,
        status: VehicleStatus,
        fuel_type: FuelType,
        transmission: Transmission,
        current_mileage: int,
        purchase_price: Decimal | None,
        purchase_date: date | None,
        insurance_expiry: date | None,
        inspection_expiry: date | None,
        gps_device_id: str | None,
        current_latitude: Decimal | None,
        current_longitude: Decimal | None,
        current_fuel_level: int | None,
        branch_id: BranchId | None,
        photos: list[str] | None,
        features: dict[str, Any] | None,
        pricing_override: dict[str, Any] | None,
        created_at: UtcDatetime,
        updated_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.nickname = nickname
        self.make = make
        self.model = model
        self.year = year
        self.vin = vin
        self.license_plate = license_plate
        self.color = color
        self.category = category
        self.status = status
        self.fuel_type = fuel_type
        self.transmission = transmission
        self.current_mileage = current_mileage
        self.purchase_price = purchase_price
        self.purchase_date = purchase_date
        self.insurance_expiry = insurance_expiry
        self.inspection_expiry = inspection_expiry
        self.gps_device_id = gps_device_id
        self.current_latitude = current_latitude
        self.current_longitude = current_longitude
        self.current_fuel_level = current_fuel_level
        self.branch_id = branch_id
        self.photos = photos
        self.features = features
        self.pricing_override = pricing_override
        self._created_at = created_at
        self.updated_at = updated_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
