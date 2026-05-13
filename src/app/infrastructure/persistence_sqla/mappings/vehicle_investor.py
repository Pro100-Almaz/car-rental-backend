from enum import StrEnum

from sqlalchemy import UUID, Column, DateTime, Enum, ForeignKey, Numeric, Table
from sqlalchemy.orm import composite

from app.core.common.entities.types_ import ProfitDistributionType
from app.core.common.entities.vehicle_investor import VehicleInvestor
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


vehicle_investors_table = Table(
    "vehicle_investors",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "vehicle_id",
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "investor_id",
        UUID(as_uuid=True),
        ForeignKey("investors.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("share_percentage", Numeric(5, 2), nullable=False),
    Column(
        "profit_distribution_type",
        Enum(
            ProfitDistributionType,
            name="profit_distribution_type",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_vehicle_investors_table() -> None:
    mapper_registry.map_imperatively(
        VehicleInvestor,
        vehicle_investors_table,
        properties={
            "id_": vehicle_investors_table.c.id,
            "vehicle_id": vehicle_investors_table.c.vehicle_id,
            "investor_id": vehicle_investors_table.c.investor_id,
            "share_percentage": vehicle_investors_table.c.share_percentage,
            "profit_distribution_type": vehicle_investors_table.c.profit_distribution_type,
            "_created_at": composite(UtcDatetime, vehicle_investors_table.c.created_at),
        },
        column_prefix="__",
    )
