from datetime import datetime
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.queries.list_mobile_vehicles import ListMobileVehicles, ListMobileVehiclesRequest
from app.core.queries.ports.mobile_vehicle_reader import ListMobileVehiclesQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_list_vehicles_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/vehicles",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_vehicles(
        interactor: FromDishka[ListMobileVehicles],
        organization_id: Annotated[UUID, Query(...)],
        category: Annotated[str | None, Query()] = None,
        fuel_type: Annotated[str | None, Query()] = None,
        transmission: Annotated[str | None, Query()] = None,
        branch_id: Annotated[UUID | None, Query()] = None,
        search: Annotated[str | None, Query()] = None,
        date_from: Annotated[datetime | None, Query()] = None,
        date_to: Annotated[datetime | None, Query()] = None,
    ) -> ListMobileVehiclesQm:
        return await interactor.execute(
            ListMobileVehiclesRequest(
                organization_id=organization_id,
                category=category,
                fuel_type=fuel_type,
                transmission=transmission,
                branch_id=branch_id,
                search=search,
                date_from=date_from,
                date_to=date_to,
            )
        )

    return router
