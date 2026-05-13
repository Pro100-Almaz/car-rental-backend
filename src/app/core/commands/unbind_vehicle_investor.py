import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import VehicleInvestorNotFoundError
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.vehicle_investor_tx_storage import VehicleInvestorTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import VehicleInvestorId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UnbindVehicleInvestorRequest:
    vehicle_investor_id: UUID


class UnbindVehicleInvestor:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        vehicle_investor_tx_storage: VehicleInvestorTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._vehicle_investor_tx_storage = vehicle_investor_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UnbindVehicleInvestorRequest) -> None:
        logger.info("Unbind vehicle from investor: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="investor.update",
            ),
        )

        vi_id = VehicleInvestorId(request.vehicle_investor_id)
        vehicle_investor = await self._vehicle_investor_tx_storage.get_by_id(vi_id, for_update=True)
        if vehicle_investor is None:
            raise VehicleInvestorNotFoundError

        await self._vehicle_investor_tx_storage.delete(vehicle_investor)
        await self._transaction_manager.commit()

        logger.info("Unbind vehicle from investor: done.")
