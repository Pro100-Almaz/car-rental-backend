import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.additional_service_tx_storage import AdditionalServiceTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.additional_service import AdditionalService
from app.core.common.entities.types_ import OrganizationId
from app.core.common.factories.id_factory import create_additional_service_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateAdditionalServiceRequest:
    organization_id: UUID
    name: str
    price: Decimal
    is_active: bool = True


class CreateAdditionalServiceResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateAdditionalService:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        additional_service_tx_storage: AdditionalServiceTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._additional_service_tx_storage = additional_service_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateAdditionalServiceRequest) -> CreateAdditionalServiceResponse:
        logger.info("Create additional service: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        additional_service = AdditionalService(
            id_=create_additional_service_id(),
            organization_id=OrganizationId(request.organization_id),
            name=request.name,
            price=request.price,
            is_active=request.is_active,
            created_at=now,
        )
        self._additional_service_tx_storage.add(additional_service)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create additional service: done.")
        return CreateAdditionalServiceResponse(
            id=additional_service.id_,
            created_at=additional_service.created_at.value,
        )
