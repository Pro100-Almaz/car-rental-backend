import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.expense_category_tx_storage import ExpenseCategoryTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.expense_category import ExpenseCategory
from app.core.common.entities.types_ import ExpenseCategoryType, OrganizationId
from app.core.common.factories.id_factory import create_expense_category_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateExpenseCategoryRequest:
    organization_id: UUID
    name: str
    type_: ExpenseCategoryType
    is_system: bool = False
    sort_order: int = 0
    is_active: bool = True


class CreateExpenseCategoryResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateExpenseCategory:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        expense_category_tx_storage: ExpenseCategoryTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._expense_category_tx_storage = expense_category_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateExpenseCategoryRequest) -> CreateExpenseCategoryResponse:
        logger.info("Create expense category: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="finance.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        expense_category = ExpenseCategory(
            id_=create_expense_category_id(),
            organization_id=OrganizationId(request.organization_id),
            name=request.name,
            type_=request.type_,
            is_system=request.is_system,
            sort_order=request.sort_order,
            is_active=request.is_active,
            created_at=now,
        )
        self._expense_category_tx_storage.add(expense_category)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create expense category: done.")
        return CreateExpenseCategoryResponse(
            id=expense_category.id_,
            created_at=expense_category.created_at.value,
        )
