import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import CashJournalEntryNotFoundError
from app.core.commands.update_cash_journal_entry import UpdateCashJournalEntry, UpdateCashJournalEntryRequest
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class UpdateCashJournalEntryBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: datetime.date | None = None
    operation_type: str | None = None
    vehicle_id: UUID | None = None
    rental_id: UUID | None = None
    expense_category_id: UUID | None = None
    payment_method: str | None = None
    amount: Decimal | None = None
    description: str | None = None
    receipt_url: str | None = None


def make_update_entry_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{entry_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            CashJournalEntryNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def update_entry(
        entry_id: UUID,
        body: UpdateCashJournalEntryBody,
        interactor: FromDishka[UpdateCashJournalEntry],
    ) -> None:
        kwargs: dict[str, Any] = {"entry_id": entry_id}
        for field_name in body.model_fields_set:
            kwargs[field_name] = getattr(body, field_name)
        request = UpdateCashJournalEntryRequest(**kwargs)
        await interactor.execute(request)

    return router
