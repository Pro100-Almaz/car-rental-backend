import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.commands.exceptions import InvalidTaskStatusTransitionError, ServiceTaskNotFoundError
from app.core.commands.ports.service_task_tx_storage import ServiceTaskTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import ServiceTaskId, TaskStatus
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CompleteServiceTaskRequest:
    service_task_id: UUID
    actual_cost: Decimal | None = None
    proof_photos: list[Any] | None = None
    notes: str | None = None


class CompleteServiceTask:
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

    async def execute(self, request: CompleteServiceTaskRequest) -> None:
        logger.info("Complete service task: started.")

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

        if task.status not in {TaskStatus.PHOTO_PROOF, TaskStatus.IN_PROGRESS}:
            raise InvalidTaskStatusTransitionError(
                f"Complete requires status 'photo_proof' or 'in_progress', got '{task.status}'."
            )

        now = self._utc_timer.now.value
        task.status = TaskStatus.COMPLETED
        task.completed_at = now
        if request.actual_cost is not None:
            task.actual_cost = request.actual_cost
        if request.proof_photos is not None:
            task.proof_photos = request.proof_photos
        if request.notes is not None:
            task.notes = request.notes
        task.updated_at = UtcDatetime(now)
        await self._transaction_manager.commit()

        logger.info("Complete service task: done.")
