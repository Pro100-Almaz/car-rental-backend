from typing import Protocol

from app.core.common.entities.service_task import ServiceTask
from app.core.common.entities.types_ import ServiceTaskId


class ServiceTaskTxStorage(Protocol):
    def add(self, service_task: ServiceTask) -> None: ...

    async def get_by_id(
        self,
        service_task_id: ServiceTaskId,
        *,
        for_update: bool = False,
    ) -> ServiceTask | None: ...
