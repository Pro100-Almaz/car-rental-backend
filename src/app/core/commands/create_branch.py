import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.exceptions import OrganizationNotFoundError
from app.core.commands.ports.branch_tx_storage import BranchTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.organization_tx_storage import OrganizationTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.entities.branch import Branch
from app.core.common.entities.types_ import OrganizationId
from app.core.common.factories.id_factory import create_branch_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateBranchRequest:
    organization_id: UUID
    name: str
    address: str
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    timezone: str = "Asia/Almaty"


class CreateBranchResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateBranch:
    def __init__(
        self,
        utc_timer: UtcTimer,
        organization_tx_storage: OrganizationTxStorage,
        branch_tx_storage: BranchTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._utc_timer = utc_timer
        self._organization_tx_storage = organization_tx_storage
        self._branch_tx_storage = branch_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateBranchRequest) -> CreateBranchResponse:
        logger.info("Create branch: started.")

        organization_id = OrganizationId(request.organization_id)
        organization = await self._organization_tx_storage.get_by_id(organization_id)
        if organization is None:
            raise OrganizationNotFoundError

        now = UtcDatetime(self._utc_timer.now.value)
        branch = Branch(
            id_=create_branch_id(),
            organization_id=organization_id,
            name=request.name,
            address=request.address,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone=request.timezone,
            created_at=now,
        )
        self._branch_tx_storage.add(branch)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create branch: done.")
        return CreateBranchResponse(
            id=branch.id_,
            created_at=branch.created_at.value,
        )
