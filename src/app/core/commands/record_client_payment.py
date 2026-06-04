import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.exceptions import ClientNotFoundError
from app.core.commands.ports.client_tx_storage import ClientTxStorage
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
    TransactionSource,
    TransactionStatus,
    TransactionType,
)
from app.core.common.exceptions import BaseError
from app.core.common.factories.id_factory import create_transaction_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

MAX_CLIENT_NOTE_LEN = 2000


class InvalidPaymentAmountError(BaseError):
    default_message: str = "Payment amount must be positive."


@dataclass(frozen=True, slots=True, kw_only=True)
class RecordClientPaymentRequest:
    organization_id: UUID
    rental_id: UUID | None = None
    type: TransactionType
    amount: Decimal
    payment_method: PaymentMethod
    client_note: str | None = None


class RecordClientPaymentResponse(TypedDict):
    id: UUID
    created_at: datetime


class RecordClientPayment:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        client_tx_storage: ClientTxStorage,
        payment_tx_storage: PaymentTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._client_tx_storage = client_tx_storage
        self._payment_tx_storage = payment_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: RecordClientPaymentRequest) -> RecordClientPaymentResponse:
        logger.info("Record client payment: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.payments",
            ),
        )

        if request.amount <= Decimal(0):
            raise InvalidPaymentAmountError
        if request.client_note and len(request.client_note) > MAX_CLIENT_NOTE_LEN:
            raise InvalidPaymentAmountError(f"Client note cannot exceed {MAX_CLIENT_NOTE_LEN} characters.")

        client = await self._client_tx_storage.get_by_id(ClientId(current_user.client_id))
        if client is None:
            raise ClientNotFoundError

        now = UtcDatetime(self._utc_timer.now.value)
        transaction = Transaction(
            id_=create_transaction_id(),
            organization_id=OrganizationId(request.organization_id),
            rental_id=RentalId(request.rental_id) if request.rental_id else None,
            client_id=client.id_,
            type_=request.type,
            amount=request.amount,
            currency="KZT",
            payment_method=request.payment_method,
            status=TransactionStatus.PENDING,
            external_id=None,
            metadata=None,
            source=TransactionSource.MOBILE,
            client_note=request.client_note,
            rejection_reason=None,
            created_at=now,
            updated_at=now,
        )
        self._payment_tx_storage.add(transaction)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Record client payment: done.")
        return RecordClientPaymentResponse(
            id=transaction.id_,
            created_at=transaction.created_at.value,
        )
