from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    BookingType,
    ClientId,
    DepositStatus,
    DepositType,
    OrganizationId,
    PrepaymentStatus,
    RateType,
    RentalId,
    RentalStatus,
    UserId,
    VehicleId,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class Rental(Entity[RentalId]):
    def __init__(
        self,
        *,
        id_: RentalId,
        organization_id: OrganizationId,
        vehicle_id: VehicleId,
        client_id: ClientId,
        manager_id: UserId | None,
        status: RentalStatus,
        booking_type: BookingType,
        booked_at: datetime,
        scheduled_start: datetime,
        scheduled_end: datetime,
        actual_start: datetime | None,
        actual_end: datetime | None,
        base_rate: Decimal,
        rate_type: RateType,
        estimated_total: Decimal,
        actual_total: Decimal | None,
        discount_code: str | None,
        discount_amount: Decimal,
        late_fee: Decimal,
        mileage_surcharge: Decimal,
        fuel_charge: Decimal,
        wash_fee: Decimal,
        damage_charge: Decimal,
        fine_charge: Decimal,
        deposit_type: DepositType,
        deposit_amount: Decimal,
        deposit_status: DepositStatus,
        deposit_refund_amount: Decimal,
        checkin_data: dict[str, Any] | None,
        checkout_data: dict[str, Any] | None,
        invoice_url: str | None,
        cancellation_reason: str | None,
        prepayment_amount: Decimal,
        prepayment_status: PrepaymentStatus,
        notes: str | None,
        created_at: UtcDatetime,
        updated_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.vehicle_id = vehicle_id
        self.client_id = client_id
        self.manager_id = manager_id
        self.status = status
        self.booking_type = booking_type
        self.booked_at = booked_at
        self.scheduled_start = scheduled_start
        self.scheduled_end = scheduled_end
        self.actual_start = actual_start
        self.actual_end = actual_end
        self.base_rate = base_rate
        self.rate_type = rate_type
        self.estimated_total = estimated_total
        self.actual_total = actual_total
        self.discount_code = discount_code
        self.discount_amount = discount_amount
        self.late_fee = late_fee
        self.mileage_surcharge = mileage_surcharge
        self.fuel_charge = fuel_charge
        self.wash_fee = wash_fee
        self.damage_charge = damage_charge
        self.fine_charge = fine_charge
        self.deposit_type = deposit_type
        self.deposit_amount = deposit_amount
        self.deposit_status = deposit_status
        self.deposit_refund_amount = deposit_refund_amount
        self.checkin_data = checkin_data
        self.checkout_data = checkout_data
        self.invoice_url = invoice_url
        self.cancellation_reason = cancellation_reason
        self.prepayment_amount = prepayment_amount
        self.prepayment_status = prepayment_status
        self.notes = notes
        self._created_at = created_at
        self.updated_at = updated_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
