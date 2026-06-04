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


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfirmClientPaymentRequest:
    transaction_id: UUID


class ConfirmClientPayment:
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

    async def execute(self, request: ConfirmClientPaymentRequest) -> None:
        logger.info("Confirm client payment: started.")

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

        if transaction.status != TransactionStatus.PENDING:
            raise InvalidTransactionStatusTransitionError(
                f"Cannot confirm transaction with status '{transaction.status}'."
            )

        transaction.status = TransactionStatus.COMPLETED
        transaction.updated_at = UtcDatetime(self._utc_timer.now.value)
        await self._transaction_manager.commit()

        logger.info("Confirm client payment: done.")
