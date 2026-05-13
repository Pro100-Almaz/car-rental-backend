import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.investor_tx_storage import InvestorTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.investor import Investor
from app.core.common.entities.types_ import InvestorType, OrganizationId, UserId
from app.core.common.factories.id_factory import create_investor_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateInvestorRequest:
    organization_id: UUID
    full_name: str
    type_: InvestorType
    contact_phone: str | None = None
    contact_email: str | None = None
    user_id: UUID | None = None
    notes: str | None = None


class CreateInvestorResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateInvestor:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        investor_tx_storage: InvestorTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._investor_tx_storage = investor_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateInvestorRequest) -> CreateInvestorResponse:
        logger.info("Create investor: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="investor.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        investor = Investor(
            id_=create_investor_id(),
            organization_id=OrganizationId(request.organization_id),
            full_name=request.full_name,
            type_=request.type_,
            contact_phone=request.contact_phone,
            contact_email=request.contact_email,
            user_id=UserId(request.user_id) if request.user_id else None,
            notes=request.notes,
            created_at=now,
            updated_at=now,
        )
        self._investor_tx_storage.add(investor)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create investor: done.")
        return CreateInvestorResponse(
            id=investor.id_,
            created_at=investor.created_at.value,
        )
