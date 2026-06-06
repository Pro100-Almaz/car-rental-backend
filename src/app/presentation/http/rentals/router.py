from fastapi import APIRouter

from app.presentation.http.rentals.approve_extension import make_approve_extension_router
from app.presentation.http.rentals.cancel_rental import make_cancel_rental_router
from app.presentation.http.rentals.checkin_rental import make_checkin_rental_router
from app.presentation.http.rentals.checkout_rental import make_checkout_rental_router
from app.presentation.http.rentals.complete_rental import make_complete_rental_router
from app.presentation.http.rentals.create_rental import make_create_rental_router
from app.presentation.http.rentals.extend_rental import make_extend_rental_router
from app.presentation.http.rentals.get_rental import make_get_rental_router
from app.presentation.http.rentals.get_rental_calendar import make_get_rental_calendar_router
from app.presentation.http.rentals.get_returns_queue import make_get_returns_queue_router
from app.presentation.http.rentals.list_booking_requests import make_list_booking_requests_router
from app.presentation.http.rentals.list_pending_extensions import make_list_pending_extensions_router
from app.presentation.http.rentals.list_rentals import make_list_rentals_router
from app.presentation.http.rentals.reject_extension import make_reject_extension_router
from app.presentation.http.rentals.transition_rental import make_transition_rental_router
from app.presentation.http.rentals.update_rental import make_update_rental_router


def make_rentals_router() -> APIRouter:
    router = APIRouter(
        prefix="/rentals",
        tags=["Rentals"],
    )
    # Literal-path routes MUST be registered before the `/{rental_id}` parametric
    # routes. Otherwise FastAPI matches `/{rental_id}` first and tries to parse the
    # literal segment as a UUID (e.g. "extension-requests" → 422 UUID error).
    router.include_router(make_create_rental_router())
    router.include_router(make_list_booking_requests_router())
    router.include_router(make_get_rental_calendar_router())
    router.include_router(make_get_returns_queue_router())
    router.include_router(make_list_rentals_router())
    router.include_router(make_list_pending_extensions_router())
    router.include_router(make_get_rental_router())
    router.include_router(make_update_rental_router())
    router.include_router(make_transition_rental_router())
    router.include_router(make_checkin_rental_router())
    router.include_router(make_checkout_rental_router())
    router.include_router(make_extend_rental_router())
    router.include_router(make_cancel_rental_router())
    router.include_router(make_complete_rental_router())
    router.include_router(make_approve_extension_router())
    router.include_router(make_reject_extension_router())
    return router
