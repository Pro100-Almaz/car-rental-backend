import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import RentalServiceNotFoundError
from app.core.commands.ports.rental_service_tx_storage import RentalServiceTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import RentalServiceId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class RemoveRentalServiceRequest:
    rental_service_id: UUID


class RemoveRentalService:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        rental_service_tx_storage: RentalServiceTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._rental_service_tx_storage = rental_service_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: RemoveRentalServiceRequest) -> None:
        logger.info("Remove rental service: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="rental.update",
            ),
        )

        rental_service_id = RentalServiceId(request.rental_service_id)
        rental_service = await self._rental_service_tx_storage.get_by_id(rental_service_id, for_update=True)
        if rental_service is None:
            raise RentalServiceNotFoundError

        await self._rental_service_tx_storage.delete(rental_service)
        await self._transaction_manager.commit()

        logger.info("Remove rental service: done.")
