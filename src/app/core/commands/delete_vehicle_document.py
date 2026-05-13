import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.vehicle_document_tx_storage import VehicleDocumentTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext

logger = logging.getLogger(__name__)


class VehicleDocumentNotFoundError(Exception):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteVehicleDocumentRequest:
    document_id: UUID


class DeleteVehicleDocument:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        vehicle_document_tx_storage: VehicleDocumentTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._storage = vehicle_document_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: DeleteVehicleDocumentRequest) -> None:
        logger.info("Delete vehicle document: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.update",
            ),
        )

        document = await self._storage.get_by_id(request.document_id)
        if document is None:
            raise VehicleDocumentNotFoundError

        await self._storage.delete(document)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Delete vehicle document: done.")
