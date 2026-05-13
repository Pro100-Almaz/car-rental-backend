from typing import Annotated, Any
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.create_vehicle_category import (
    CreateVehicleCategory,
    CreateVehicleCategoryRequest,
    CreateVehicleCategoryResponse,
)
from app.core.commands.update_vehicle_category import (
    UpdateVehicleCategory,
    UpdateVehicleCategoryRequest,
    VehicleCategoryNotFoundError,
)
from app.core.common.exceptions import BusinessTypeError
from app.core.queries.list_vehicle_categories import ListVehicleCategories, ListVehicleCategoriesRequest
from app.core.queries.models.vehicle_category import ListVehicleCategoriesQm
from app.infrastructure.exceptions import ReaderError, StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ListVehicleCategoriesSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    organization_id: UUID


class UpdateVehicleCategoryBody(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


def make_vehicle_categories_router() -> APIRouter:
    router = ErrorAwareRouter(prefix="/vehicle-categories", tags=["Vehicle Categories"])

    @router.post(
        "/",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
        },
        default_on_error=log_info,
        status_code=status.HTTP_201_CREATED,
    )
    @inject
    async def create_vehicle_category(
        request: CreateVehicleCategoryRequest,
        interactor: FromDishka[CreateVehicleCategory],
    ) -> CreateVehicleCategoryResponse:
        return await interactor.execute(request)

    @router.get(
        "/",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_vehicle_categories(
        request_schema: Annotated[ListVehicleCategoriesSchema, Depends()],
        interactor: FromDishka[ListVehicleCategories],
    ) -> ListVehicleCategoriesQm:
        return await interactor.execute(
            ListVehicleCategoriesRequest(organization_id=request_schema.organization_id)
        )

    @router.patch(
        "/{category_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            VehicleCategoryNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def update_vehicle_category(
        category_id: UUID,
        body: UpdateVehicleCategoryBody,
        interactor: FromDishka[UpdateVehicleCategory],
    ) -> None:
        fields_set = body.model_fields_set
        kwargs: dict[str, Any] = {"category_id": category_id}
        for field_name in UpdateVehicleCategoryBody.model_fields:
            if field_name in fields_set:
                kwargs[field_name] = getattr(body, field_name)
        request = UpdateVehicleCategoryRequest(**kwargs)
        await interactor.execute(request)

    return router
