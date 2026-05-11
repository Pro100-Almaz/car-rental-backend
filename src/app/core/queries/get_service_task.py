import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.service_task import ServiceTaskQm
from app.core.queries.ports.service_task_reader import ServiceTaskReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetServiceTaskRequest:
    service_task_id: UUID


class GetServiceTask:
    def __init__(
        self,
        service_task_reader: ServiceTaskReader,
    ) -> None:
        self._service_task_reader = service_task_reader

    async def execute(self, request: GetServiceTaskRequest) -> ServiceTaskQm | None:
        logger.info("Get service task: started.")

        result = await self._service_task_reader.get_by_id(
            service_task_id=request.service_task_id,
        )

        logger.info("Get service task: done.")
        return result
