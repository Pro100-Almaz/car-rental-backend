from datetime import datetime
from uuid import UUID

from sqlalchemy import case, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.returns_queue import ReturnsQueueItemQm, ReturnsQueueQm
from app.core.queries.ports.returns_queue_reader import ReturnsQueueReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.client import clients_table
from app.infrastructure.persistence_sqla.mappings.rental import rentals_table
from app.infrastructure.persistence_sqla.mappings.vehicle import vehicles_table

_ACTIVE_STATUSES = ("active", "returning")


class SqlaReturnsQueueReader(ReturnsQueueReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_returns_queue(
        self,
        *,
        organization_id: UUID,
        now: datetime,
        horizon: datetime,
    ) -> ReturnsQueueQm:
        is_overdue = case(
            (
                (rentals_table.c.scheduled_end < now) & (rentals_table.c.status == "active"),
                True,
            ),
            else_=False,
        ).label("is_overdue")

        stmt = (
            select(
                rentals_table.c.id.label("rental_id"),
                rentals_table.c.vehicle_id,
                vehicles_table.c.nickname.label("vehicle_nickname"),
                vehicles_table.c.license_plate.label("vehicle_license_plate"),
                rentals_table.c.client_id,
                (clients_table.c.first_name + " " + clients_table.c.last_name).label("client_name"),
                rentals_table.c.status,
                rentals_table.c.scheduled_start,
                rentals_table.c.scheduled_end,
                rentals_table.c.estimated_total,
                is_overdue,
            )
            .join(vehicles_table, rentals_table.c.vehicle_id == vehicles_table.c.id)
            .join(clients_table, rentals_table.c.client_id == clients_table.c.id)
            .where(
                rentals_table.c.organization_id == organization_id,
                rentals_table.c.status.in_(_ACTIVE_STATUSES),
                rentals_table.c.scheduled_end <= horizon,
            )
            .order_by(rentals_table.c.scheduled_end.asc())
        )

        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e

        items = [
            ReturnsQueueItemQm(
                rental_id=row.rental_id,
                vehicle_id=row.vehicle_id,
                vehicle_nickname=row.vehicle_nickname,
                vehicle_license_plate=row.vehicle_license_plate,
                client_id=row.client_id,
                client_name=row.client_name,
                status=row.status,
                scheduled_start=row.scheduled_start,
                scheduled_end=row.scheduled_end,
                estimated_total=row.estimated_total,
                is_overdue=row.is_overdue,
            )
            for row in rows
        ]

        return ReturnsQueueQm(items=items, total=len(items))
