from decimal import Decimal
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.complete_rental import CompleteRental, CompleteRentalRequest
from app.core.commands.exceptions import InvalidRentalStatusTransitionError, RentalNotFoundError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class CompleteRentalBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    actual_total: Decimal
    late_fee: Decimal = Decimal(0)
    mileage_surcharge: Decimal = Decimal(0)
    fuel_charge: Decimal = Decimal(0)
    wash_fee: Decimal = Decimal(0)
    damage_charge: Decimal = Decimal(0)
    fine_charge: Decimal = Decimal(0)
    deposit_refund_amount: Decimal = Decimal(0)


def make_complete_rental_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{rental_id}/complete",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RentalNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidRentalStatusTransitionError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def complete_rental(
        rental_id: UUID,
        body: CompleteRentalBody,
        interactor: FromDishka[CompleteRental],
    ) -> None:
        request = CompleteRentalRequest(
            rental_id=rental_id,
            actual_total=body.actual_total,
            late_fee=body.late_fee,
            mileage_surcharge=body.mileage_surcharge,
            fuel_charge=body.fuel_charge,
            wash_fee=body.wash_fee,
            damage_charge=body.damage_charge,
            fine_charge=body.fine_charge,
            deposit_refund_amount=body.deposit_refund_amount,
        )
        await interactor.execute(request)

    return router
