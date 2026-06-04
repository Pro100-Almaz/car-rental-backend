from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import ClientNotFoundError
from app.core.common.authorization.exceptions import AuthorizationError
from app.core.queries.list_my_organizations import ListMyOrganizations
from app.core.queries.ports.client_organization_reader import ListClientOrganizationsQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_list_my_organizations_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/organizations",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ClientNotFoundError: status.HTTP_404_NOT_FOUND,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_my_organizations(
        interactor: FromDishka[ListMyOrganizations],
    ) -> ListClientOrganizationsQm:
        return await interactor.execute()

    return router
