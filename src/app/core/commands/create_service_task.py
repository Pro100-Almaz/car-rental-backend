import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.service_task_tx_storage import ServiceTaskTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.service_task import ServiceTask
from app.core.common.entities.types_ import (
    OrganizationId,
    RentalId,
    ServiceTaskType,
    TaskPriority,
    TaskStatus,
    UserId,
    VehicleId,
)
from app.core.common.factories.id_factory import create_service_task_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateServiceTaskRequest:
    organization_id: UUID
    vehicle_id: UUID
    rental_id: UUID | None = None
    assigned_to: UUID | None = None
    task_type: ServiceTaskType
    priority: TaskPriority
    description: str | None = None
    estimated_cost: Decimal | None = None
    due_at: datetime | None = None


class CreateServiceTaskResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateServiceTask:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        service_task_tx_storage: ServiceTaskTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._service_task_tx_storage = service_task_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateServiceTaskRequest) -> CreateServiceTaskResponse:
        logger.info("Create service task: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="task.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        task = ServiceTask(
            id_=create_service_task_id(),
            organization_id=OrganizationId(request.organization_id),
            vehicle_id=VehicleId(request.vehicle_id),
            rental_id=RentalId(request.rental_id) if request.rental_id else None,
            assigned_to=UserId(request.assigned_to) if request.assigned_to else None,
            task_type=request.task_type,
            priority=request.priority,
            status=TaskStatus.CREATED,
            description=request.description,
            estimated_cost=request.estimated_cost,
            actual_cost=None,
            proof_photos=None,
            notes=None,
            due_at=request.due_at,
            completed_at=None,
            created_at=now,
            updated_at=now,
        )
        self._service_task_tx_storage.add(task)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create service task: done.")
        return CreateServiceTaskResponse(
            id=task.id_,
            created_at=task.created_at.value,
        )
