import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.service_task_reader import ListServiceTasksQm, ServiceTaskReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListServiceTasksRequest:
    organization_id: UUID
    vehicle_id: UUID | None = None
    assigned_to: UUID | None = None
    status: str | None = None
    priority: str | None = None


class ListServiceTasks:
    def __init__(
        self,
        service_task_reader: ServiceTaskReader,
    ) -> None:
        self._service_task_reader = service_task_reader

    async def execute(self, request: ListServiceTasksRequest) -> ListServiceTasksQm:
        logger.info("List service tasks: started.")

        result = await self._service_task_reader.list_service_tasks(
            organization_id=request.organization_id,
            vehicle_id=request.vehicle_id,
            assigned_to=request.assigned_to,
            status=request.status,
            priority=request.priority,
        )

        logger.info("List service tasks: done.")
        return result
