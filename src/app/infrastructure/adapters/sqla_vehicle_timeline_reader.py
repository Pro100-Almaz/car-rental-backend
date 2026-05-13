from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, union_all, literal, cast, String, DateTime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.vehicle_timeline import VehicleTimelineEventQm, VehicleTimelineQm
from app.core.queries.ports.vehicle_timeline_reader import VehicleTimelineReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.cash_journal_entry import cash_journal_table
from app.infrastructure.persistence_sqla.mappings.fine import fines_table
from app.infrastructure.persistence_sqla.mappings.rental import rentals_table
from app.infrastructure.persistence_sqla.mappings.service_task import service_tasks_table


class SqlaVehicleTimelineReader(VehicleTimelineReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_timeline(
        self,
        *,
        vehicle_id: UUID,
    ) -> VehicleTimelineQm:
        rentals_q = (
            select(
                rentals_table.c.id,
                literal("rental").label("event_type"),
                cast(rentals_table.c.created_at, DateTime(timezone=True)).label("event_date"),
                (literal("Rental — ") + cast(rentals_table.c.status, String)).label("title"),
                rentals_table.c.notes.label("description"),
                rentals_table.c.actual_total.label("amount"),
            )
            .where(rentals_table.c.vehicle_id == vehicle_id)
        )

        expenses_q = (
            select(
                cash_journal_table.c.id,
                literal("expense").label("event_type"),
                cast(cash_journal_table.c.created_at, DateTime(timezone=True)).label("event_date"),
                (literal("Expense — ") + cast(cash_journal_table.c.operation_type, String)).label("title"),
                cash_journal_table.c.description.label("description"),
                cash_journal_table.c.amount.label("amount"),
            )
            .where(cash_journal_table.c.vehicle_id == vehicle_id)
        )

        fines_q = (
            select(
                fines_table.c.id,
                literal("fine").label("event_type"),
                cast(fines_table.c.created_at, DateTime(timezone=True)).label("event_date"),
                (literal("Fine — ") + cast(fines_table.c.fine_type, String)).label("title"),
                fines_table.c.description.label("description"),
                fines_table.c.amount.label("amount"),
            )
            .where(fines_table.c.vehicle_id == vehicle_id)
        )

        tasks_q = (
            select(
                service_tasks_table.c.id,
                literal("service_task").label("event_type"),
                cast(service_tasks_table.c.created_at, DateTime(timezone=True)).label("event_date"),
                (literal("Task — ") + cast(service_tasks_table.c.task_type, String)).label("title"),
                service_tasks_table.c.description.label("description"),
                service_tasks_table.c.estimated_cost.label("amount"),
            )
            .where(service_tasks_table.c.vehicle_id == vehicle_id)
        )

        combined = union_all(rentals_q, expenses_q, fines_q, tasks_q).subquery()
        stmt = select(combined).order_by(combined.c.event_date.desc())

        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e

        events = [
            VehicleTimelineEventQm(
                id=row.id,
                event_type=row.event_type,
                event_date=row.event_date,
                title=row.title,
                description=row.description,
                amount=Decimal(str(row.amount)) if row.amount is not None else None,
                metadata=None,
            )
            for row in rows
        ]
        return VehicleTimelineQm(events=events, total=len(events))
