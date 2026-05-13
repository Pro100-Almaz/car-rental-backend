from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import InvestorNotFoundError
from app.core.commands.ports.investor_tx_storage import InvestorTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import InvestorId, InvestorType, UserId
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

_UNSET = object()


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateInvestorRequest:
    investor_id: UUID
    full_name: str | object = _UNSET
    type_: InvestorType | object = _UNSET
    contact_phone: str | None | object = _UNSET
    contact_email: str | None | object = _UNSET
    user_id: UUID | None | object = _UNSET
    notes: str | None | object = _UNSET


class UpdateInvestor:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        investor_tx_storage: InvestorTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._investor_tx_storage = investor_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateInvestorRequest) -> None:
        logger.info("Update investor: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="investor.update",
            ),
        )

        investor_id = InvestorId(request.investor_id)
        investor = await self._investor_tx_storage.get_by_id(investor_id, for_update=True)
        if investor is None:
            raise InvestorNotFoundError

        changed = False
        for attr in ("full_name", "type_", "contact_phone", "contact_email", "notes"):
            val = getattr(request, attr)
            if val is not _UNSET and val != getattr(investor, attr):
                setattr(investor, attr, val)
                changed = True

        user_val = request.user_id
        if user_val is not _UNSET:
            new_user_id = UserId(user_val) if user_val is not None else None  # type: ignore[arg-type]
            if new_user_id != investor.user_id:
                investor.user_id = new_user_id
                changed = True

        if changed:
            investor.updated_at = UtcDatetime(self._utc_timer.now.value)
            await self._transaction_manager.commit()

        logger.info("Update investor: done.")
