import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.rental_service_tx_storage import RentalServiceTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.rental_service import RentalService
from app.core.common.entities.types_ import AdditionalServiceId, RentalId
from app.core.common.factories.id_factory import create_rental_service_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class AddRentalServiceRequest:
    rental_id: UUID
    service_id: UUID
    quantity: int = 1
    price: Decimal


class AddRentalServiceResponse(TypedDict):
    id: UUID


class AddRentalService:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        rental_service_tx_storage: RentalServiceTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._rental_service_tx_storage = rental_service_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: AddRentalServiceRequest) -> AddRentalServiceResponse:
        logger.info("Add rental service: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="rental.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        rental_service = RentalService(
            id_=create_rental_service_id(),
            rental_id=RentalId(request.rental_id),
            service_id=AdditionalServiceId(request.service_id),
            quantity=request.quantity,
            price=request.price,
            created_at=now,
        )
        self._rental_service_tx_storage.add(rental_service)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Add rental service: done.")
        return AddRentalServiceResponse(
            id=rental_service.id_,
        )
