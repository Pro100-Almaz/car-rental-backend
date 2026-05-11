import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, TypedDict
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.payment_tx_storage import PaymentTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.transaction import Transaction
from app.core.common.entities.types_ import (
    ClientId,
    OrganizationId,
    PaymentMethod,
    RentalId,
    TransactionStatus,
    TransactionType,
)
from app.core.common.factories.id_factory import create_transaction_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessRefundRequest:
    organization_id: UUID
    rental_id: UUID | None = None
    client_id: UUID
    amount: Decimal
    payment_method: PaymentMethod
    currency: str = "KZT"
    external_id: str | None = None
    metadata: dict[str, Any] | None = None


class ProcessRefundResponse(TypedDict):
    id: UUID
    created_at: datetime


class ProcessRefund:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        payment_tx_storage: PaymentTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._payment_tx_storage = payment_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: ProcessRefundRequest) -> ProcessRefundResponse:
        logger.info("Process refund: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="payment.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        transaction = Transaction(
            id_=create_transaction_id(),
            organization_id=OrganizationId(request.organization_id),
            rental_id=RentalId(request.rental_id) if request.rental_id else None,
            client_id=ClientId(request.client_id),
            type_=TransactionType.DEPOSIT_REFUND,
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method,
            status=TransactionStatus.PENDING,
            external_id=request.external_id,
            metadata=request.metadata,
            created_at=now,
            updated_at=now,
        )
        self._payment_tx_storage.add(transaction)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Process refund: done.")
        return ProcessRefundResponse(
            id=transaction.id_,
            created_at=transaction.created_at.value,
        )
