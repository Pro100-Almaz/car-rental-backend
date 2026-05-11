from enum import StrEnum

from sqlalchemy import UUID, Column, DateTime, Enum, ForeignKey, Numeric, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import composite

from app.core.common.entities.rental import Rental
from app.core.common.entities.types_ import (
    BookingType,
    DepositStatus,
    DepositType,
    PrepaymentStatus,
    RateType,
    RentalStatus,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


rentals_table = Table(
    "rentals",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "vehicle_id",
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "client_id",
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "manager_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column(
        "status",
        Enum(
            RentalStatus,
            name="rental_status",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column(
        "booking_type",
        Enum(
            BookingType,
            name="booking_type",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    # Timing
    Column("booked_at", DateTime(timezone=True), nullable=False),
    Column("scheduled_start", DateTime(timezone=True), nullable=False),
    Column("scheduled_end", DateTime(timezone=True), nullable=False),
    Column("actual_start", DateTime(timezone=True), nullable=True),
    Column("actual_end", DateTime(timezone=True), nullable=True),
    # Pricing
    Column("base_rate", Numeric(10, 2), nullable=False),
    Column(
        "rate_type",
        Enum(
            RateType,
            name="rate_type",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("estimated_total", Numeric(10, 2), nullable=False),
    Column("actual_total", Numeric(10, 2), nullable=True),
    Column("discount_code", String(50), nullable=True),
    Column("discount_amount", Numeric(10, 2), nullable=False, default=0),
    Column("late_fee", Numeric(10, 2), nullable=False, default=0),
    Column("mileage_surcharge", Numeric(10, 2), nullable=False, default=0),
    Column("fuel_charge", Numeric(10, 2), nullable=False, default=0),
    Column("wash_fee", Numeric(10, 2), nullable=False, default=0),
    Column("damage_charge", Numeric(10, 2), nullable=False, default=0),
    Column("fine_charge", Numeric(10, 2), nullable=False, default=0),
    # Deposit
    Column(
        "deposit_type",
        Enum(
            DepositType,
            name="deposit_type",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("deposit_amount", Numeric(10, 2), nullable=False),
    Column(
        "deposit_status",
        Enum(
            DepositStatus,
            name="deposit_status",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("deposit_refund_amount", Numeric(10, 2), nullable=False, default=0),
    # Inspection
    Column("checkin_data", JSONB, nullable=True),
    Column("checkout_data", JSONB, nullable=True),
    # Final
    Column("invoice_url", String(500), nullable=True),
    Column("cancellation_reason", Text, nullable=True),
    Column("prepayment_amount", Numeric(10, 2), nullable=False, default=0),
    Column(
        "prepayment_status",
        Enum(
            PrepaymentStatus,
            name="prepayment_status",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("notes", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


def map_rentals_table() -> None:
    mapper_registry.map_imperatively(
        Rental,
        rentals_table,
        properties={
            "id_": rentals_table.c.id,
            "organization_id": rentals_table.c.organization_id,
            "vehicle_id": rentals_table.c.vehicle_id,
            "client_id": rentals_table.c.client_id,
            "manager_id": rentals_table.c.manager_id,
            "status": rentals_table.c.status,
            "booking_type": rentals_table.c.booking_type,
            "booked_at": rentals_table.c.booked_at,
            "scheduled_start": rentals_table.c.scheduled_start,
            "scheduled_end": rentals_table.c.scheduled_end,
            "actual_start": rentals_table.c.actual_start,
            "actual_end": rentals_table.c.actual_end,
            "base_rate": rentals_table.c.base_rate,
            "rate_type": rentals_table.c.rate_type,
            "estimated_total": rentals_table.c.estimated_total,
            "actual_total": rentals_table.c.actual_total,
            "discount_code": rentals_table.c.discount_code,
            "discount_amount": rentals_table.c.discount_amount,
            "late_fee": rentals_table.c.late_fee,
            "mileage_surcharge": rentals_table.c.mileage_surcharge,
            "fuel_charge": rentals_table.c.fuel_charge,
            "wash_fee": rentals_table.c.wash_fee,
            "damage_charge": rentals_table.c.damage_charge,
            "fine_charge": rentals_table.c.fine_charge,
            "deposit_type": rentals_table.c.deposit_type,
            "deposit_amount": rentals_table.c.deposit_amount,
            "deposit_status": rentals_table.c.deposit_status,
            "deposit_refund_amount": rentals_table.c.deposit_refund_amount,
            "checkin_data": rentals_table.c.checkin_data,
            "checkout_data": rentals_table.c.checkout_data,
            "invoice_url": rentals_table.c.invoice_url,
            "cancellation_reason": rentals_table.c.cancellation_reason,
            "prepayment_amount": rentals_table.c.prepayment_amount,
            "prepayment_status": rentals_table.c.prepayment_status,
            "notes": rentals_table.c.notes,
            "_created_at": composite(UtcDatetime, rentals_table.c.created_at),
            "updated_at": composite(UtcDatetime, rentals_table.c.updated_at),
        },
        column_prefix="__",
    )
