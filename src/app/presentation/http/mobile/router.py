from fastapi import APIRouter

from app.presentation.http.mobile.cancel_my_rental import make_cancel_my_rental_router
from app.presentation.http.mobile.check_availability import make_check_availability_router
from app.presentation.http.mobile.get_my_active_rental import make_get_my_active_rental_router
from app.presentation.http.mobile.get_my_fines import make_get_my_fines_router
from app.presentation.http.mobile.get_my_outstanding import make_get_my_outstanding_router
from app.presentation.http.mobile.get_my_payments import make_get_my_payments_router
from app.presentation.http.mobile.get_my_profile import make_get_my_profile_router
from app.presentation.http.mobile.get_my_rental import make_get_my_rental_router
from app.presentation.http.mobile.get_my_verification import make_get_my_verification_router
from app.presentation.http.mobile.get_vehicle import make_get_vehicle_router
from app.presentation.http.mobile.join_organization import make_join_organization_router
from app.presentation.http.mobile.leave_organization import make_leave_organization_router
from app.presentation.http.mobile.list_my_notifications import make_list_my_notifications_router
from app.presentation.http.mobile.list_my_organizations import make_list_my_organizations_router
from app.presentation.http.mobile.list_my_rentals import make_list_my_rentals_router
from app.presentation.http.mobile.list_vehicles import make_list_vehicles_router
from app.presentation.http.mobile.mark_notification_read import make_mark_notification_read_router
from app.presentation.http.mobile.record_payment import make_record_payment_router
from app.presentation.http.mobile.register_device import make_register_device_router
from app.presentation.http.mobile.submit_booking import make_submit_booking_router
from app.presentation.http.mobile.submit_extension_request import make_submit_extension_request_router
from app.presentation.http.mobile.unregister_device import make_unregister_device_router
from app.presentation.http.mobile.update_my_profile import make_update_my_profile_router
from app.presentation.http.mobile.update_notification_preferences import make_update_notification_preferences_router
from app.presentation.http.mobile.upload_document import make_upload_document_router


def make_mobile_router() -> APIRouter:
    router = APIRouter(
        prefix="/mobile",
        tags=["Mobile"],
    )
    # Profile
    router.include_router(make_get_my_profile_router())
    router.include_router(make_update_my_profile_router())
    router.include_router(make_get_my_verification_router())
    router.include_router(make_upload_document_router())
    router.include_router(make_get_my_fines_router())
    router.include_router(make_get_my_payments_router())
    router.include_router(make_get_my_outstanding_router())
    router.include_router(make_update_notification_preferences_router())
    # Notifications
    router.include_router(make_list_my_notifications_router())
    router.include_router(make_mark_notification_read_router())
    # Devices
    router.include_router(make_register_device_router())
    router.include_router(make_unregister_device_router())
    # Organizations
    router.include_router(make_list_my_organizations_router())
    router.include_router(make_join_organization_router())
    router.include_router(make_leave_organization_router())
    # Vehicles
    router.include_router(make_list_vehicles_router())
    router.include_router(make_get_vehicle_router())
    router.include_router(make_check_availability_router())
    # Rentals — active must come before {rental_id} to avoid path conflict
    router.include_router(make_get_my_active_rental_router())
    router.include_router(make_list_my_rentals_router())
    router.include_router(make_get_my_rental_router())
    router.include_router(make_submit_booking_router())
    router.include_router(make_cancel_my_rental_router())
    router.include_router(make_submit_extension_request_router())
    # Payments
    router.include_router(make_record_payment_router())
    return router
