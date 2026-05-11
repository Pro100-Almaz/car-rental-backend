import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import InvalidTransactionStatusTransitionError, TransactionNotFoundError
from app.core.commands.ports.payment_tx_storage import PaymentTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import TransactionId, TransactionStatus
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

VALID_TRANSACTION_TRANSITIONS: dict[TransactionStatus, set[TransactionStatus]] = {
    TransactionStatus.PENDING: {TransactionStatus.PROCESSING, TransactionStatus.COMPLETED, TransactionStatus.FAILED},
    TransactionStatus.PROCESSING: {TransactionStatus.COMPLETED, TransactionStatus.FAILED},
    TransactionStatus.COMPLETED: {TransactionStatus.REFUNDED},
    TransactionStatus.FAILED: set(),
    TransactionStatus.REFUNDED: set(),
}


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateTransactionStatusRequest:
    transaction_id: UUID
    status: TransactionStatus
    external_id: str | None = None


class UpdateTransactionStatus:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        payment_tx_storage: PaymentTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._payment_tx_storage = payment_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateTransactionStatusRequest) -> None:
        logger.info("Update transaction status: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="payment.update",
            ),
        )

        transaction_id = TransactionId(request.transaction_id)
        transaction = await self._payment_tx_storage.get_by_id(transaction_id, for_update=True)
        if transaction is None:
            raise TransactionNotFoundError

        allowed = VALID_TRANSACTION_TRANSITIONS.get(transaction.status, set())
        if request.status not in allowed:
            raise InvalidTransactionStatusTransitionError(
                f"Cannot transition from '{transaction.status}' to '{request.status}'."
            )

        transaction.status = request.status
        if request.external_id is not None:
            transaction.external_id = request.external_id
        transaction.updated_at = UtcDatetime(self._utc_timer.now.value)
        await self._transaction_manager.commit()

        logger.info("Update transaction status: done.")
