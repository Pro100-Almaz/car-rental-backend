from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import ExpenseCategoryNotFoundError
from app.core.commands.ports.expense_category_tx_storage import ExpenseCategoryTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import ExpenseCategoryId, ExpenseCategoryType

logger = logging.getLogger(__name__)

_UNSET = object()


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateExpenseCategoryRequest:
    expense_category_id: UUID
    name: str | object = _UNSET
    type_: ExpenseCategoryType | object = _UNSET
    sort_order: int | object = _UNSET
    is_active: bool | object = _UNSET


class UpdateExpenseCategory:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        expense_category_tx_storage: ExpenseCategoryTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._expense_category_tx_storage = expense_category_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateExpenseCategoryRequest) -> None:
        logger.info("Update expense category: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="finance.update",
            ),
        )

        expense_category_id = ExpenseCategoryId(request.expense_category_id)
        expense_category = await self._expense_category_tx_storage.get_by_id(expense_category_id, for_update=True)
        if expense_category is None:
            raise ExpenseCategoryNotFoundError

        changed = False
        for attr in ("name", "type_", "sort_order", "is_active"):
            val = getattr(request, attr)
            if val is not _UNSET and val != getattr(expense_category, attr):
                setattr(expense_category, attr, val)
                changed = True

        if changed:
            await self._transaction_manager.commit()

        logger.info("Update expense category: done.")
