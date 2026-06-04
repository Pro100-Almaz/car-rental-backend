import logging
from dataclasses import dataclass

from app.core.commands.ports.device_token_tx_storage import DeviceTokenTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import UserId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UnregisterDeviceTokenRequest:
    token: str


class UnregisterDeviceToken:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        device_token_tx_storage: DeviceTokenTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._device_token_tx_storage = device_token_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UnregisterDeviceTokenRequest) -> None:
        logger.info("Unregister device token: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.devices",
            ),
        )

        await self._device_token_tx_storage.delete_by_token(
            request.token,
            UserId(current_user.id_),
        )
        await self._transaction_manager.commit()

        logger.info("Unregister device token: done.")
