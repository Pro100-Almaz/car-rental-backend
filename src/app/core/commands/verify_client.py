import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import ClientNotFoundError
from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import ClientId, VerificationStatus
from app.core.common.services.trust_score import TRUST_EVENTS, get_trust_level
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class VerifyClientRequest:
    client_id: UUID
    status: VerificationStatus


class VerifyClient:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        client_tx_storage: ClientTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._client_tx_storage = client_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: VerifyClientRequest) -> None:
        logger.info("Verify client: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="client.update",
            ),
        )

        client_id = ClientId(request.client_id)
        client = await self._client_tx_storage.get_by_id(client_id, for_update=True)
        if client is None:
            raise ClientNotFoundError

        client.verification_status = request.status

        if request.status == VerificationStatus.VERIFIED:
            client.trust_score += TRUST_EVENTS["document_verified"]
            client.trust_level = get_trust_level(client.trust_score)

        client.updated_at = UtcDatetime(self._utc_timer.now.value)
        await self._transaction_manager.commit()

        logger.info("Verify client: done.")
