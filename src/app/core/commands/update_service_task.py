from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.core.commands.exceptions import InvalidTaskStatusTransitionError, ServiceTaskNotFoundError
from app.core.commands.ports.service_task_tx_storage import ServiceTaskTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.task_transitions import VALID_TASK_TRANSITIONS
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.service_task import ServiceTask
from app.core.common.entities.types_ import ServiceTaskId, TaskPriority, TaskStatus, UserId
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

_UNSET = object()


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateServiceTaskRequest:
    service_task_id: UUID
    assigned_to: UUID | None | object = _UNSET
    priority: TaskPriority | object = _UNSET
    status: TaskStatus | object = _UNSET
    description: str | None | object = _UNSET
    estimated_cost: Decimal | None | object = _UNSET
    actual_cost: Decimal | None | object = _UNSET
    notes: str | None | object = _UNSET
    due_at: datetime | None | object = _UNSET


class UpdateServiceTask:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        service_task_tx_storage: ServiceTaskTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._service_task_tx_storage = service_task_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateServiceTaskRequest) -> None:
        logger.info("Update service task: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="task.update",
            ),
        )

        task_id = ServiceTaskId(request.service_task_id)
        task = await self._service_task_tx_storage.get_by_id(task_id, for_update=True)
        if task is None:
            raise ServiceTaskNotFoundError

        self._apply_fields(request, task)

        task.updated_at = UtcDatetime(self._utc_timer.now.value)
        await self._transaction_manager.commit()

        logger.info("Update service task: done.")

    @staticmethod
    def _apply_fields(
        request: UpdateServiceTaskRequest,
        task: ServiceTask,
    ) -> None:
        if request.status is not _UNSET:
            new_status: TaskStatus = request.status  # type: ignore[assignment]
            allowed = VALID_TASK_TRANSITIONS.get(task.status, set())
            if new_status not in allowed:
                raise InvalidTaskStatusTransitionError(f"Cannot transition from '{task.status}' to '{new_status}'.")
            task.status = new_status

        if request.assigned_to is not _UNSET:
            val = request.assigned_to
            task.assigned_to = UserId(val) if val is not None else None  # type: ignore[arg-type]

        if request.priority is not _UNSET:
            task.priority = request.priority  # type: ignore[assignment]

        if request.description is not _UNSET:
            task.description = request.description  # type: ignore[assignment]

        if request.estimated_cost is not _UNSET:
            task.estimated_cost = request.estimated_cost  # type: ignore[assignment]

        if request.actual_cost is not _UNSET:
            task.actual_cost = request.actual_cost  # type: ignore[assignment]

        if request.notes is not _UNSET:
            task.notes = request.notes  # type: ignore[assignment]

        if request.due_at is not _UNSET:
            task.due_at = request.due_at  # type: ignore[assignment]
