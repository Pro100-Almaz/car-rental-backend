from fastapi import APIRouter

from app.presentation.http.rentals.cancel_rental import make_cancel_rental_router
from app.presentation.http.rentals.checkin_rental import make_checkin_rental_router
from app.presentation.http.rentals.checkout_rental import make_checkout_rental_router
from app.presentation.http.rentals.complete_rental import make_complete_rental_router
from app.presentation.http.rentals.create_rental import make_create_rental_router
from app.presentation.http.rentals.extend_rental import make_extend_rental_router
from app.presentation.http.rentals.get_rental import make_get_rental_router
from app.presentation.http.rentals.list_rentals import make_list_rentals_router


def make_rentals_router() -> APIRouter:
    router = APIRouter(
        prefix="/rentals",
        tags=["Rentals"],
    )
    router.include_router(make_create_rental_router())
    router.include_router(make_list_rentals_router())
    router.include_router(make_get_rental_router())
    router.include_router(make_checkin_rental_router())
    router.include_router(make_checkout_rental_router())
    router.include_router(make_extend_rental_router())
    router.include_router(make_cancel_rental_router())
    router.include_router(make_complete_rental_router())
    return router
