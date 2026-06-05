import calendar
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

from app.core.queries.get_cash_flow import GetCashFlow, GetCashFlowRequest
from app.core.queries.get_company_pnl import GetCompanyPnl, GetCompanyPnlRequest
from app.core.queries.get_vehicles_comparison import GetVehiclesComparison, GetVehiclesComparisonRequest
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def _parse_period(
    period: str | None,
    date_from: datetime.date | None,
    date_to: datetime.date | None,
) -> tuple[datetime.date, datetime.date]:
    if period is not None:
        year, month = int(period[:4]), int(period[5:7])
        return datetime.date(year, month, 1), datetime.date(year, month, calendar.monthrange(year, month)[1])
    if date_from is not None and date_to is not None:
        return date_from, date_to
    today = datetime.datetime.now(tz=datetime.UTC).date()
    return (
        datetime.date(today.year, today.month, 1),
        datetime.date(today.year, today.month, calendar.monthrange(today.year, today.month)[1]),
    )


def make_export_router() -> APIRouter:  # noqa: PLR0915 - TODO: split per-report-type into helpers (see ROADMAP)
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
    async def export_report(
        organization_id: Annotated[UUID, Query(...)],
        report_type: Annotated[str, Query(alias="type", description="pnl, cash-flow, or vehicles-comparison")],
        period: Annotated[str | None, Query()] = None,
        date_from: Annotated[datetime.date | None, Query(alias="from")] = None,
        date_to: Annotated[datetime.date | None, Query(alias="to")] = None,
        pnl_interactor: FromDishka[GetCompanyPnl] = ...,  # type: ignore[assignment]
        cf_interactor: FromDishka[GetCashFlow] = ...,  # type: ignore[assignment]
        vc_interactor: FromDishka[GetVehiclesComparison] = ...,  # type: ignore[assignment]
    ) -> StreamingResponse:
        d_from, d_to = _parse_period(period, date_from, date_to)
        wb = Workbook()
        ws = wb.active

        if report_type == "pnl":
            result = await pnl_interactor.execute(
                GetCompanyPnlRequest(organization_id=organization_id, date_from=d_from, date_to=d_to)
            )
            ws.title = "P&L"
            ws.append(["Company P&L", f"{d_from} — {d_to}"])
            ws.append([])
            ws.append(["Total Revenue", float(result.total_revenue)])
            ws.append(["Returns & Discounts", float(result.returns_and_discounts)])
            ws.append(["Net Revenue", float(result.net_revenue)])
            ws.append([])
            ws.append(["Direct Expenses"])
            for line in result.direct_expenses:
                ws.append([f"  {line.category_name}", float(line.amount)])
            ws.append(["Total Direct Expenses", float(result.total_direct_expenses)])
            ws.append(["Marginal Profit", float(result.marginal_profit)])
            ws.append([])
            ws.append(["Overhead Expenses"])
            for line in result.overhead_expenses:
                ws.append([f"  {line.category_name}", float(line.amount)])
            ws.append(["Total Overhead Expenses", float(result.total_overhead_expenses)])
            ws.append(["Operating Profit", float(result.operating_profit)])
            ws.append(["Taxes", float(result.taxes)])
            ws.append(["Net Profit", float(result.net_profit)])
            ws.append(["Investor Payouts", float(result.investor_payouts)])
            ws.append(["Retained Profit", float(result.retained_profit)])

        elif report_type == "cash-flow":
            result = await cf_interactor.execute(
                GetCashFlowRequest(organization_id=organization_id, date_from=d_from, date_to=d_to)
            )
            ws.title = "Cash Flow"
            ws.append(["Cash Flow", f"{d_from} — {d_to}"])
            ws.append([])
            ws.append(["Opening Balance", float(result.opening_balance)])
            ws.append(["Total Income", float(result.total_income)])
            ws.append(["Total Expense", float(result.total_expense)])
            ws.append(["Closing Balance", float(result.closing_balance)])
            ws.append([])
            ws.append(["Date", "Income", "Expense", "Net"])
            for day in result.daily_breakdown:
                ws.append([day.date, float(day.income), float(day.expense), float(day.net)])

        elif report_type == "vehicles-comparison":
            result = await vc_interactor.execute(
                GetVehiclesComparisonRequest(organization_id=organization_id, date_from=d_from, date_to=d_to)
            )
            ws.title = "Vehicles"
            headers = [
                "Vehicle",
                "License Plate",
                "Revenue",
                *result.expense_categories,
                "Total Expenses",
                "Net Profit",
                "Utilization %",
            ]
            ws.append(headers)
            for v in result.vehicles:
                row = [
                    v.nickname or "",
                    v.license_plate,
                    float(v.total_revenue),
                ]
                row.extend(float(exp.amount) for exp in v.expenses)
                row.extend([float(v.total_expenses), float(v.net_profit), float(v.utilization_percent)])
                ws.append(row)

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        filename = f"report_{report_type}_{d_from}_{d_to}.xlsx"
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return router
