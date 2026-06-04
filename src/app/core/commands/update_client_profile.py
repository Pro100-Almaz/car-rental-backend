import logging
from dataclasses import dataclass

from app.core.commands.exceptions import ClientNotFoundError
from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import ClientId
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

_UNSET = object()


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateClientProfileRequest:
    first_name: str | object = _UNSET
    last_name: str | object = _UNSET
    phone: str | object = _UNSET


class UpdateClientProfile:
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

    async def execute(self, request: UpdateClientProfileRequest) -> None:
        logger.info("Update client profile: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.profile",
            ),
        )

        if current_user.client_id is None:
            raise ClientNotFoundError

        client = await self._client_tx_storage.get_by_id(
            ClientId(current_user.client_id),
            for_update=True,
        )
        if client is None:
            raise ClientNotFoundError

        if request.first_name is not _UNSET:
            client.first_name = request.first_name  # type: ignore[assignment]
        if request.last_name is not _UNSET:
            client.last_name = request.last_name  # type: ignore[assignment]
        if request.phone is not _UNSET:
            client.phone = request.phone  # type: ignore[assignment]

        client.updated_at = UtcDatetime(self._utc_timer.now.value)
        await self._transaction_manager.commit()

        logger.info("Update client profile: done.")
