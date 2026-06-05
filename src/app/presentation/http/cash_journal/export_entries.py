import datetime
import io
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse
from fastapi_error_map import ErrorAwareRouter
from openpyxl import Workbook

from app.core.queries.list_cash_journal_entries import ListCashJournalEntries, ListCashJournalEntriesRequest
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE

HEADERS = [
    "Date",
    "Type",
    "Vehicle ID",
    "Rental ID",
    "Category ID",
    "Payment Method",
    "Amount",
    "Description",
    "Confirmed By",
    "Confirmed At",
    "Created By",
    "Created At",
]


def make_export_entries_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/export",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
    )
    @inject
    async def export_entries(
        organization_id: Annotated[UUID, Query(...)],
        operation_type: Annotated[str | None, Query()] = None,
        vehicle_id: Annotated[UUID | None, Query()] = None,
        expense_category_id: Annotated[UUID | None, Query()] = None,
        payment_method: Annotated[str | None, Query()] = None,
        date_from: Annotated[datetime.date | None, Query()] = None,
        date_to: Annotated[datetime.date | None, Query()] = None,
        interactor: FromDishka[ListCashJournalEntries] = ...,  # type: ignore[assignment]
    ) -> StreamingResponse:
        request = ListCashJournalEntriesRequest(
            organization_id=organization_id,
            operation_type=operation_type,
            vehicle_id=vehicle_id,
            expense_category_id=expense_category_id,
            payment_method=payment_method,
            date_from=date_from,
            date_to=date_to,
        )
        result = await interactor.execute(request)

        wb = Workbook()
        ws = wb.active
        ws.title = "Cash Journal"
        ws.append(HEADERS)

        for entry in result["entries"]:
            ws.append(
                [
                    str(entry.date),
                    entry.operation_type,
                    str(entry.vehicle_id) if entry.vehicle_id else "",
                    str(entry.rental_id) if entry.rental_id else "",
                    str(entry.expense_category_id) if entry.expense_category_id else "",
                    entry.payment_method,
                    float(entry.amount),
                    entry.description or "",
                    str(entry.confirmed_by) if entry.confirmed_by else "",
                    str(entry.confirmed_at) if entry.confirmed_at else "",
                    str(entry.created_by),
                    str(entry.created_at),
                ]
            )

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        filename = f"cash_journal_{datetime.datetime.now(tz=datetime.UTC).date().isoformat()}.xlsx"
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return router
