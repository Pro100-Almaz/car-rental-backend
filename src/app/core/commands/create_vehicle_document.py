import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.ports.vehicle_document_tx_storage import VehicleDocumentTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import VehicleId
from app.core.common.entities.vehicle_document import VehicleDocument
from app.core.common.factories.id_factory import create_vehicle_document_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateVehicleDocumentRequest:
    vehicle_id: UUID
    document_type: str
    name: str
    url: str
    expiry_date: date | None = None


class CreateVehicleDocumentResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateVehicleDocument:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        vehicle_document_tx_storage: VehicleDocumentTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._storage = vehicle_document_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateVehicleDocumentRequest) -> CreateVehicleDocumentResponse:
        logger.info("Create vehicle document: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.update",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        document = VehicleDocument(
            id_=create_vehicle_document_id(),
            vehicle_id=VehicleId(request.vehicle_id),
            document_type=request.document_type,
            name=request.name,
            url=request.url,
            expiry_date=request.expiry_date,
            created_at=now,
        )
        self._storage.add(document)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create vehicle document: done.")
        return CreateVehicleDocumentResponse(
            id=document.id_,
            created_at=document.created_at.value,
        )
