import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.investor_payout_tx_storage import InvestorPayoutTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.investor_payout import InvestorPayout
from app.core.common.entities.types_ import InvestorId, OrganizationId, PayoutStatus
from app.core.common.factories.id_factory import create_investor_payout_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateInvestorPayoutRequest:
    organization_id: UUID
    investor_id: UUID
    period_month: date
    calculated_profit: Decimal
    share_amount: Decimal
    notes: str | None = None


class CreateInvestorPayoutResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateInvestorPayout:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        investor_payout_tx_storage: InvestorPayoutTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._investor_payout_tx_storage = investor_payout_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateInvestorPayoutRequest) -> CreateInvestorPayoutResponse:
        logger.info("Create investor payout: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="investor.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        payout = InvestorPayout(
            id_=create_investor_payout_id(),
            organization_id=OrganizationId(request.organization_id),
            investor_id=InvestorId(request.investor_id),
            period_month=request.period_month,
            calculated_profit=request.calculated_profit,
            share_amount=request.share_amount,
            status=PayoutStatus.CALCULATED,
            paid_at=None,
            notes=request.notes,
            created_at=now,
        )
        self._investor_payout_tx_storage.add(payout)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create investor payout: done.")
        return CreateInvestorPayoutResponse(
            id=payout.id_,
            created_at=payout.created_at.value,
        )
