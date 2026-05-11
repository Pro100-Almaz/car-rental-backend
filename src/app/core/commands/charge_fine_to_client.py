import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import FineNotFoundError
from app.core.commands.ports.fine_tx_storage import FineTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import ClientId, FineId, FineStatus
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ChargeFineToClientRequest:
    fine_id: UUID
    client_id: UUID


class ChargeFineToClient:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        fine_tx_storage: FineTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._fine_tx_storage = fine_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: ChargeFineToClientRequest) -> None:
        logger.info("Charge fine to client: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fine.update",
            ),
        )

        fine_id = FineId(request.fine_id)
        fine = await self._fine_tx_storage.get_by_id(fine_id, for_update=True)
        if fine is None:
            raise FineNotFoundError

        fine.client_id = ClientId(request.client_id)
        fine.status = FineStatus.CHARGED_TO_CLIENT
        fine.updated_at = UtcDatetime(self._utc_timer.now.value)
        await self._transaction_manager.commit()

        logger.info("Charge fine to client: done.")
