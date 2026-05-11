from fastapi import APIRouter

from app.presentation.http.organizations.create_organization import make_create_organization_router
from app.presentation.http.organizations.list_organizations import make_list_organizations_router


def make_organizations_router() -> APIRouter:
    router = APIRouter(
        prefix="/organizations",
        tags=["Organizations"],
    )
    router.include_router(make_create_organization_router())
    router.include_router(make_list_organizations_router())
    return router
