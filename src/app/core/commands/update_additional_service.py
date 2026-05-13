from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.core.commands.exceptions import AdditionalServiceNotFoundError
from app.core.commands.ports.additional_service_tx_storage import AdditionalServiceTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import AdditionalServiceId

logger = logging.getLogger(__name__)

_UNSET = object()


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateAdditionalServiceRequest:
    additional_service_id: UUID
    name: str | object = _UNSET
    price: Decimal | object = _UNSET
    is_active: bool | object = _UNSET


class UpdateAdditionalService:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        additional_service_tx_storage: AdditionalServiceTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._additional_service_tx_storage = additional_service_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateAdditionalServiceRequest) -> None:
        logger.info("Update additional service: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.update",
            ),
        )

        additional_service_id = AdditionalServiceId(request.additional_service_id)
        additional_service = await self._additional_service_tx_storage.get_by_id(additional_service_id, for_update=True)
        if additional_service is None:
            raise AdditionalServiceNotFoundError

        changed = False
        for attr in ("name", "price", "is_active"):
            val = getattr(request, attr)
            if val is not _UNSET and val != getattr(additional_service, attr):
                setattr(additional_service, attr, val)
                changed = True

        if changed:
            await self._transaction_manager.commit()

        logger.info("Update additional service: done.")
