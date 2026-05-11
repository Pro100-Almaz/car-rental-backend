from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.service_task import ServiceTaskQm
from app.core.queries.ports.service_task_reader import ListServiceTasksQm, ServiceTaskReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.service_task import service_tasks_table


class SqlaServiceTaskReader(ServiceTaskReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            service_tasks_table.c.id,
            service_tasks_table.c.organization_id,
            service_tasks_table.c.vehicle_id,
            service_tasks_table.c.rental_id,
            service_tasks_table.c.assigned_to,
            service_tasks_table.c.task_type,
            service_tasks_table.c.priority,
            service_tasks_table.c.status,
            service_tasks_table.c.description,
            service_tasks_table.c.estimated_cost,
            service_tasks_table.c.actual_cost,
            service_tasks_table.c.proof_photos,
            service_tasks_table.c.notes,
            service_tasks_table.c.due_at,
            service_tasks_table.c.completed_at,
            service_tasks_table.c.created_at,
            service_tasks_table.c.updated_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> ServiceTaskQm:
        return ServiceTaskQm(
            id=row.id,
            organization_id=row.organization_id,
            vehicle_id=row.vehicle_id,
            rental_id=row.rental_id,
            assigned_to=row.assigned_to,
            task_type=row.task_type,
            priority=row.priority,
            status=row.status,
            description=row.description,
            estimated_cost=row.estimated_cost,
            actual_cost=row.actual_cost,
            proof_photos=row.proof_photos,
            notes=row.notes,
            due_at=row.due_at,
            completed_at=row.completed_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(
        self,
        *,
        service_task_id: UUID,
    ) -> ServiceTaskQm | None:
        stmt = select(*self._base_columns()).where(
            service_tasks_table.c.id == service_task_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)

    async def list_service_tasks(
        self,
        *,
        organization_id: UUID,
        vehicle_id: UUID | None = None,
        assigned_to: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
    ) -> ListServiceTasksQm:
        stmt = (
            select(*self._base_columns())
            .where(service_tasks_table.c.organization_id == organization_id)
            .order_by(service_tasks_table.c.created_at.desc())
        )
        if vehicle_id is not None:
            stmt = stmt.where(service_tasks_table.c.vehicle_id == vehicle_id)
        if assigned_to is not None:
            stmt = stmt.where(service_tasks_table.c.assigned_to == assigned_to)
        if status is not None:
            stmt = stmt.where(service_tasks_table.c.status == status)
        if priority is not None:
            stmt = stmt.where(service_tasks_table.c.priority == priority)
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        tasks = [self._row_to_qm(row) for row in rows]
        return ListServiceTasksQm(
            service_tasks=tasks,
            total=len(tasks),
        )
