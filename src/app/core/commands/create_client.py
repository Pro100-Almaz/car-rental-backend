import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, TypedDict
from uuid import UUID

from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.client import Client
from app.core.common.entities.types_ import OrganizationId, TrustLevel, VerificationStatus
from app.core.common.factories.id_factory import create_client_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateClientRequest:
    organization_id: UUID
    phone: str
    email: str | None = None
    first_name: str
    last_name: str
    id_document_url: str | None = None
    license_front_url: str | None = None
    license_back_url: str | None = None
    metadata: dict[str, Any] | None = None


class CreateClientResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateClient:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        client_tx_storage: ClientTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._client_tx_storage = client_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateClientRequest) -> CreateClientResponse:
        logger.info("Create client: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="client.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        client = Client(
            id_=create_client_id(),
            organization_id=OrganizationId(request.organization_id),
            user_id=None,
            phone=request.phone,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            id_document_url=request.id_document_url,
            license_front_url=request.license_front_url,
            license_back_url=request.license_back_url,
            verification_status=VerificationStatus.PENDING,
            trust_score=0,
            trust_level=TrustLevel.NEW,
            is_blacklisted=False,
            blacklist_reason=None,
            wallet_balance=Decimal(0),
            debt_balance=Decimal(0),
            metadata=request.metadata,
            created_at=now,
            updated_at=now,
        )
        self._client_tx_storage.add(client)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create client: done.")
        return CreateClientResponse(
            id=client.id_,
            created_at=client.created_at.value,
        )
