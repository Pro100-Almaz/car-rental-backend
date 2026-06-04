from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MobileRentalQm:
    id: UUID
    organization_id: UUID
    vehicle_id: UUID
    client_id: UUID
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
    discount_amount: Decimal
    deposit_type: str
    deposit_amount: Decimal
    deposit_status: str
    deposit_refund_amount: Decimal
    prepayment_amount: Decimal
    prepayment_status: str
    source: str
    pickup_notes: str | None
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime
