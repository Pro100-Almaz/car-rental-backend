import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import VehicleNotFoundError
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.vehicle_tx_storage import VehicleTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext

logger = logging.getLogger(__name__)

MAX_PHOTOS = 10


class PhotoLimitExceededError(Exception):
    pass


class PhotoNotFoundError(Exception):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class AddVehiclePhotoRequest:
    vehicle_id: UUID
    url: str


@dataclass(frozen=True, slots=True, kw_only=True)
class RemoveVehiclePhotoRequest:
    vehicle_id: UUID
    photo_index: int


class AddVehiclePhoto:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        vehicle_tx_storage: VehicleTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._vehicle_tx_storage = vehicle_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: AddVehiclePhotoRequest) -> list[str]:
        logger.info("Add vehicle photo: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.update",
            ),
        )

        vehicle = await self._vehicle_tx_storage.get_by_id(request.vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError

        photos = list(vehicle.photos or [])
        if len(photos) >= MAX_PHOTOS:
            raise PhotoLimitExceededError

        photos.append(request.url)
        vehicle.photos = photos
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Add vehicle photo: done.")
        return photos


class RemoveVehiclePhoto:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        vehicle_tx_storage: VehicleTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._vehicle_tx_storage = vehicle_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: RemoveVehiclePhotoRequest) -> list[str]:
        logger.info("Remove vehicle photo: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.update",
            ),
        )

        vehicle = await self._vehicle_tx_storage.get_by_id(request.vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError

        photos = list(vehicle.photos or [])
        if request.photo_index < 0 or request.photo_index >= len(photos):
            raise PhotoNotFoundError

        photos.pop(request.photo_index)
        vehicle.photos = photos
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Remove vehicle photo: done.")
        return photos
