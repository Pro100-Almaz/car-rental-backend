from enum import StrEnum

from sqlalchemy import UUID, Column, Date, DateTime, Enum, ForeignKey, Numeric, Table, Text
from sqlalchemy.orm import composite

from app.core.common.entities.investor_payout import InvestorPayout
from app.core.common.entities.types_ import PayoutStatus
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


investor_payouts_table = Table(
    "investor_payouts",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "investor_id",
        UUID(as_uuid=True),
        ForeignKey("investors.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("period_month", Date, nullable=False),
    Column("calculated_profit", Numeric(12, 2), nullable=False),
    Column("share_amount", Numeric(12, 2), nullable=False),
    Column(
        "status",
        Enum(
            PayoutStatus,
            name="payout_status",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("paid_at", DateTime(timezone=True), nullable=True),
    Column("notes", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_investor_payouts_table() -> None:
    mapper_registry.map_imperatively(
        InvestorPayout,
        investor_payouts_table,
        properties={
            "id_": investor_payouts_table.c.id,
            "organization_id": investor_payouts_table.c.organization_id,
            "investor_id": investor_payouts_table.c.investor_id,
            "period_month": investor_payouts_table.c.period_month,
            "calculated_profit": investor_payouts_table.c.calculated_profit,
            "share_amount": investor_payouts_table.c.share_amount,
            "status": investor_payouts_table.c.status,
            "paid_at": investor_payouts_table.c.paid_at,
            "notes": investor_payouts_table.c.notes,
            "_created_at": composite(UtcDatetime, investor_payouts_table.c.created_at),
        },
        column_prefix="__",
    )
