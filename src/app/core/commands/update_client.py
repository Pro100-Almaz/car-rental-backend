import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

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
class UpdateClientRequest:
    client_id: UUID
    phone: str | object = _UNSET
    email: str | None | object = _UNSET
    first_name: str | object = _UNSET
    last_name: str | object = _UNSET
    id_document_url: str | None | object = _UNSET
    license_front_url: str | None | object = _UNSET
    license_back_url: str | None | object = _UNSET
    metadata: dict[str, Any] | None | object = _UNSET


class UpdateClient:
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

    async def execute(self, request: UpdateClientRequest) -> None:
        logger.info("Update client: started.")

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

        changed = False
        for attr in (
            "phone",
            "email",
            "first_name",
            "last_name",
            "id_document_url",
            "license_front_url",
            "license_back_url",
            "metadata",
        ):
            val = getattr(request, attr)
            if val is not _UNSET and val != getattr(client, attr):
                setattr(client, attr, val)
                changed = True

        if changed:
            client.updated_at = UtcDatetime(self._utc_timer.now.value)
            await self._transaction_manager.commit()

        logger.info("Update client: done.")
