import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import InvalidPayoutStatusTransitionError, InvestorPayoutNotFoundError
from app.core.commands.payout_transitions import VALID_PAYOUT_TRANSITIONS
from app.core.commands.ports.investor_payout_tx_storage import InvestorPayoutTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import InvestorPayoutId, PayoutStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdatePayoutStatusRequest:
    payout_id: UUID
    status: PayoutStatus


class UpdatePayoutStatus:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        investor_payout_tx_storage: InvestorPayoutTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._investor_payout_tx_storage = investor_payout_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdatePayoutStatusRequest) -> None:
        logger.info("Update payout status: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="investor.update",
            ),
        )

        payout_id = InvestorPayoutId(request.payout_id)
        payout = await self._investor_payout_tx_storage.get_by_id(payout_id, for_update=True)
        if payout is None:
            raise InvestorPayoutNotFoundError

        allowed = VALID_PAYOUT_TRANSITIONS.get(payout.status, set())
        if request.status not in allowed:
            raise InvalidPayoutStatusTransitionError(f"Cannot transition from '{payout.status}' to '{request.status}'.")

        payout.status = request.status
        if request.status == PayoutStatus.PAID:
            payout.paid_at = self._utc_timer.now.value
        await self._transaction_manager.commit()

        logger.info("Update payout status: done.")
