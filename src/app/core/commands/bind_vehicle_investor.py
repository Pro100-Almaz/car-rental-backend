import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.ports.vehicle_investor_tx_storage import VehicleInvestorTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import InvestorId, ProfitDistributionType, VehicleId
from app.core.common.entities.vehicle_investor import VehicleInvestor
from app.core.common.factories.id_factory import create_vehicle_investor_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class BindVehicleInvestorRequest:
    vehicle_id: UUID
    investor_id: UUID
    share_percentage: Decimal
    profit_distribution_type: ProfitDistributionType = ProfitDistributionType.PERCENTAGE


class BindVehicleInvestorResponse(TypedDict):
    id: UUID
    created_at: datetime


class BindVehicleInvestor:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        vehicle_investor_tx_storage: VehicleInvestorTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._vehicle_investor_tx_storage = vehicle_investor_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: BindVehicleInvestorRequest) -> BindVehicleInvestorResponse:
        logger.info("Bind vehicle to investor: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="investor.update",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        vehicle_investor = VehicleInvestor(
            id_=create_vehicle_investor_id(),
            vehicle_id=VehicleId(request.vehicle_id),
            investor_id=InvestorId(request.investor_id),
            share_percentage=request.share_percentage,
            profit_distribution_type=request.profit_distribution_type,
            created_at=now,
        )
        self._vehicle_investor_tx_storage.add(vehicle_investor)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Bind vehicle to investor: done.")
        return BindVehicleInvestorResponse(
            id=vehicle_investor.id_,
            created_at=vehicle_investor.created_at.value,
        )
