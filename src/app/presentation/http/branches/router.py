from fastapi import APIRouter

from app.presentation.http.branches.create_branch import make_create_branch_router
from app.presentation.http.branches.list_branches import make_list_branches_router


def make_branches_router() -> APIRouter:
    router = APIRouter(
        prefix="/branches",
        tags=["Branches"],
    )
    router.include_router(make_create_branch_router())
    router.include_router(make_list_branches_router())
    return router
