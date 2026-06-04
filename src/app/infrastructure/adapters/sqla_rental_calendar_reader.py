from collections import defaultdict
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.rental_calendar import CalendarSlotQm, CalendarVehicleQm, RentalCalendarQm
from app.core.queries.ports.rental_calendar_reader import RentalCalendarReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.client import clients_table
from app.infrastructure.persistence_sqla.mappings.rental import rentals_table
from app.infrastructure.persistence_sqla.mappings.vehicle import vehicles_table

_NON_CALENDAR_STATUSES = ("cancelled",)


class SqlaRentalCalendarReader(RentalCalendarReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_calendar(
        self,
        *,
        organization_id: UUID,
        month_start: datetime,
        month_end: datetime,
    ) -> RentalCalendarQm:
        vehicles_stmt = (
            select(
                vehicles_table.c.id,
                vehicles_table.c.nickname,
                vehicles_table.c.license_plate,
                vehicles_table.c.make,
                vehicles_table.c.model,
                vehicles_table.c.category,
            )
            .where(vehicles_table.c.organization_id == organization_id)
            .order_by(vehicles_table.c.nickname.asc(), vehicles_table.c.license_plate.asc())
        )

        rentals_stmt = (
            select(
                rentals_table.c.id.label("rental_id"),
                rentals_table.c.vehicle_id,
                rentals_table.c.client_id,
                (clients_table.c.first_name + " " + clients_table.c.last_name).label("client_name"),
                rentals_table.c.status,
                rentals_table.c.scheduled_start,
                rentals_table.c.scheduled_end,
            )
            .join(clients_table, rentals_table.c.client_id == clients_table.c.id)
            .where(
                rentals_table.c.organization_id == organization_id,
                rentals_table.c.status.notin_(_NON_CALENDAR_STATUSES),
                rentals_table.c.scheduled_start < month_end,
                rentals_table.c.scheduled_end > month_start,
            )
            .order_by(rentals_table.c.scheduled_start.asc())
        )

        try:
            vehicles_result = await self._session.execute(vehicles_stmt)
            vehicle_rows = vehicles_result.all()

            rentals_result = await self._session.execute(rentals_stmt)
            rental_rows = rentals_result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e

        slots_by_vehicle: dict[UUID, list[CalendarSlotQm]] = defaultdict(list)
        for row in rental_rows:
            slots_by_vehicle[row.vehicle_id].append(
                CalendarSlotQm(
                    rental_id=row.rental_id,
                    client_id=row.client_id,
                    client_name=row.client_name,
                    status=row.status,
                    scheduled_start=row.scheduled_start,
                    scheduled_end=row.scheduled_end,
                )
            )

        vehicles = [
            CalendarVehicleQm(
                vehicle_id=v.id,
                nickname=v.nickname,
                license_plate=v.license_plate,
                make=v.make,
                model=v.model,
                category=v.category,
                slots=slots_by_vehicle.get(v.id, []),
            )
            for v in vehicle_rows
        ]

        return RentalCalendarQm(
            vehicles=vehicles,
            month=month_start.strftime("%Y-%m"),
        )
