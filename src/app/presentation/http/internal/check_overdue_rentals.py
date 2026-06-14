"""Internal job endpoint: check-overdue-rentals."""

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from app.core.commands.check_overdue_rentals import CheckOverdueRentals
from app.core.commands.ports.organization_tx_storage import OrganizationTxStorage
from app.core.common.audit_log import emit as audit
from app.presentation.http.internal.auth import require_internal_token


class JobResult(BaseModel):
    processed: int
    notifications_sent: int


def make_check_overdue_rentals_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/check-overdue-rentals",
        status_code=status.HTTP_200_OK,
        include_in_schema=False,
        dependencies=[Depends(require_internal_token)],
    )
    @inject
    async def check_overdue_rentals(
        request: Request,
        interactor: FromDishka[CheckOverdueRentals],
        org_tx_storage: FromDishka[OrganizationTxStorage],
    ) -> JobResult:
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        audit(
            "internal.job.invoked",
            job_name="check-overdue-rentals",
            ip=client_ip,
            user_agent=user_agent,
        )
        org_ids = await org_tx_storage.list_all_ids()
        sent = 0
        for org_id in org_ids:
            sent += await interactor.execute(organization_id=org_id)
        return JobResult(processed=sent, notifications_sent=sent)

    return router
