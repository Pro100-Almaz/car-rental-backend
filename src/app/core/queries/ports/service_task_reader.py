from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.service_task import ServiceTaskQm


class ListServiceTasksQm(TypedDict):
    service_tasks: list[ServiceTaskQm]
    total: int


class ServiceTaskReader(Protocol):
    @abstractmethod
    async def get_by_id(
        self,
        *,
        service_task_id: UUID,
    ) -> ServiceTaskQm | None: ...

    @abstractmethod
    async def list_service_tasks(
        self,
        *,
        organization_id: UUID,
        vehicle_id: UUID | None = None,
        assigned_to: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
    ) -> ListServiceTasksQm: ...
