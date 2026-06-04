import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.device_token_tx_storage import DeviceTokenTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.device_token import DeviceToken
from app.core.common.entities.types_ import DevicePlatform, UserId
from app.core.common.factories.id_factory import create_device_token_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class RegisterDeviceTokenRequest:
    token: str
    platform: str
    device_name: str | None = None


class RegisterDeviceTokenResponse(TypedDict):
    id: UUID
    created_at: datetime


class RegisterDeviceToken:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        device_token_tx_storage: DeviceTokenTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._device_token_tx_storage = device_token_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: RegisterDeviceTokenRequest) -> RegisterDeviceTokenResponse:
        logger.info("Register device token: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.devices",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        platform = DevicePlatform(request.platform)

        existing = await self._device_token_tx_storage.get_by_token(request.token)
        if existing is not None:
            existing.last_active_at = now
            existing.user_id = UserId(current_user.id_)
            await self._transaction_manager.commit()
            logger.info("Register device token: updated existing token.")
            return RegisterDeviceTokenResponse(
                id=existing.id_,
                created_at=existing.created_at.value,
            )

        device_token = DeviceToken(
            id_=create_device_token_id(),
            user_id=UserId(current_user.id_),
            token=request.token,
            platform=platform,
            device_name=request.device_name,
            last_active_at=now,
            created_at=now,
        )
        self._device_token_tx_storage.add(device_token)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Register device token: done.")
        return RegisterDeviceTokenResponse(
            id=device_token.id_,
            created_at=device_token.created_at.value,
        )
