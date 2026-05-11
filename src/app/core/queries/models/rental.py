from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RentalQm:
    id: UUID
    organization_id: UUID
    vehicle_id: UUID
    client_id: UUID
    manager_id: UUID | None
    status: str
    booking_type: str
    booked_at: datetime
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: datetime | None
    actual_end: datetime | None
    base_rate: Decimal
    rate_type: str
    estimated_total: Decimal
    actual_total: Decimal | None
    discount_code: str | None
    discount_amount: Decimal
    late_fee: Decimal
    mileage_surcharge: Decimal
    fuel_charge: Decimal
    wash_fee: Decimal
    damage_charge: Decimal
    fine_charge: Decimal
    deposit_type: str
    deposit_amount: Decimal
    deposit_status: str
    deposit_refund_amount: Decimal
    checkin_data: dict[str, Any] | None
    checkout_data: dict[str, Any] | None
    invoice_url: str | None
    cancellation_reason: str | None
    prepayment_amount: Decimal
    prepayment_status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
