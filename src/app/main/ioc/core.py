from dishka import Provider, Scope, provide

from app.core.commands.activate_user import ActivateUser
from app.core.commands.add_rental_service import AddRentalService
from app.core.commands.approve_booking_request import ApproveBookingRequest
from app.core.commands.approve_extension_request import ApproveExtensionRequest
from app.core.commands.bind_vehicle_investor import BindVehicleInvestor
from app.core.commands.blacklist_client import BlacklistClient
from app.core.commands.bulk_change_vehicle_status import BulkChangeVehicleStatus
from app.core.commands.cancel_own_rental import CancelOwnRental
from app.core.commands.cancel_rental import CancelRental
from app.core.commands.change_vehicle_status import ChangeVehicleStatus
from app.core.commands.charge_client import ChargeClient
from app.core.commands.charge_fine_to_client import ChargeFineToClient
from app.core.commands.check_overdue_rentals import CheckOverdueRentals
from app.core.commands.check_pickup_reminders import CheckPickupReminders
from app.core.commands.check_return_reminders import CheckReturnReminders
from app.core.commands.checkin_rental import CheckinRental
from app.core.commands.checkout_rental import CheckoutRental
from app.core.commands.complete_rental import CompleteRental
from app.core.commands.complete_service_task import CompleteServiceTask
from app.core.commands.confirm_cash_journal_entry import ConfirmCashJournalEntry
from app.core.commands.confirm_client_payment import ConfirmClientPayment
from app.core.commands.create_additional_service import CreateAdditionalService
from app.core.commands.create_branch import CreateBranch
from app.core.commands.create_cash_journal_entry import CreateCashJournalEntry
from app.core.commands.create_client import CreateClient
from app.core.commands.create_expense_category import CreateExpenseCategory
from app.core.commands.create_fine import CreateFine
from app.core.commands.create_investor import CreateInvestor
from app.core.commands.create_investor_payout import CreateInvestorPayout
from app.core.commands.create_organization import CreateOrganization
from app.core.commands.create_rental import CreateRental
from app.core.commands.create_service_task import CreateServiceTask
from app.core.commands.create_transaction import CreateTransaction
from app.core.commands.create_user import CreateUser
from app.core.commands.create_vehicle import CreateVehicle
from app.core.commands.create_vehicle_category import CreateVehicleCategory
from app.core.commands.create_vehicle_document import CreateVehicleDocument
from app.core.commands.create_vehicle_pricing import CreateVehiclePricing
from app.core.commands.deactivate_user import DeactivateUser
from app.core.commands.delete_cash_journal_entry import DeleteCashJournalEntry
from app.core.commands.delete_vehicle_document import DeleteVehicleDocument
from app.core.commands.extend_rental import ExtendRental
from app.core.commands.hold_deposit import HoldDeposit
from app.core.commands.join_organization import JoinOrganization
from app.core.commands.leave_organization import LeaveOrganization
from app.core.commands.manage_vehicle_photos import AddVehiclePhoto, RemoveVehiclePhoto
from app.core.commands.mark_notification_read import MarkNotificationRead
from app.core.commands.ports.additional_service_tx_storage import AdditionalServiceTxStorage
from app.core.commands.ports.branch_tx_storage import BranchTxStorage
from app.core.commands.ports.cash_journal_tx_storage import CashJournalTxStorage
from app.core.commands.ports.client_organization_tx_storage import ClientOrganizationTxStorage
from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.commands.ports.device_token_tx_storage import DeviceTokenTxStorage
from app.core.commands.ports.expense_category_tx_storage import ExpenseCategoryTxStorage
from app.core.commands.ports.extension_request_tx_storage import ExtensionRequestTxStorage
from app.core.commands.ports.fine_tx_storage import FineTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.investor_payout_tx_storage import InvestorPayoutTxStorage
from app.core.commands.ports.investor_tx_storage import InvestorTxStorage
from app.core.commands.ports.notification_tx_storage import NotificationTxStorage
from app.core.commands.ports.organization_tx_storage import OrganizationTxStorage
from app.core.commands.ports.payment_tx_storage import PaymentTxStorage
from app.core.commands.ports.rental_service_tx_storage import RentalServiceTxStorage
from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.commands.ports.service_task_tx_storage import ServiceTaskTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.user_tx_storage import UserTxStorage
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.ports.vehicle_category_tx_storage import VehicleCategoryTxStorage
from app.core.commands.ports.vehicle_document_tx_storage import VehicleDocumentTxStorage
from app.core.commands.ports.vehicle_investor_tx_storage import VehicleInvestorTxStorage
from app.core.commands.ports.vehicle_pricing_tx_storage import VehiclePricingTxStorage
from app.core.commands.ports.vehicle_tx_storage import VehicleTxStorage
from app.core.commands.process_refund import ProcessRefund
from app.core.commands.record_client_payment import RecordClientPayment
from app.core.commands.register_device_token import RegisterDeviceToken
from app.core.commands.reject_booking_request import RejectBookingRequest
from app.core.commands.reject_client_payment import RejectClientPayment
from app.core.commands.reject_extension_request import RejectExtensionRequest
from app.core.commands.release_deposit import ReleaseDeposit
from app.core.commands.remove_rental_service import RemoveRentalService
from app.core.commands.send_debt_reminder import SendDebtReminder
from app.core.commands.set_user_password import SetUserPassword
from app.core.commands.set_user_role import SetUserRole
from app.core.commands.submit_booking_request import SubmitBookingRequestCommand
from app.core.commands.submit_extension_request import SubmitExtensionRequestCommand
from app.core.commands.transition_rental import TransitionRental
from app.core.commands.unbind_vehicle_investor import UnbindVehicleInvestor
from app.core.commands.unblacklist_client import UnblacklistClient
from app.core.commands.unregister_device_token import UnregisterDeviceToken
from app.core.commands.update_additional_service import UpdateAdditionalService
from app.core.commands.update_cash_journal_entry import UpdateCashJournalEntry
from app.core.commands.update_client import UpdateClient
from app.core.commands.update_client_profile import UpdateClientProfile
from app.core.commands.update_expense_category import UpdateExpenseCategory
from app.core.commands.update_investor import UpdateInvestor
from app.core.commands.update_notification_preferences import UpdateNotificationPreferences
from app.core.commands.update_organization import UpdateOrganization
from app.core.commands.update_payout_status import UpdatePayoutStatus
from app.core.commands.update_rental import UpdateRental
from app.core.commands.update_service_task import UpdateServiceTask
from app.core.commands.update_transaction_status import UpdateTransactionStatus
from app.core.commands.update_vehicle import UpdateVehicle
from app.core.commands.update_vehicle_category import UpdateVehicleCategory
from app.core.commands.update_vehicle_pricing import UpdateVehiclePricing
from app.core.commands.upload_client_document import UploadClientDocument
from app.core.commands.verify_client import VerifyClient
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.ports import AuthzUserFinder
from app.core.common.ports.access_revoker import AccessRevoker
from app.core.common.ports.identity_provider import IdentityProvider
from app.core.common.ports.password_hasher import PasswordHasher
from app.core.common.ports.push_sender import PushSender
from app.core.common.services.notification_service import NotificationService
from app.core.common.services.user import UserService
from app.core.queries.get_cash_flow import GetCashFlow
from app.core.queries.get_cash_journal_balance import GetCashJournalBalance
from app.core.queries.get_cash_journal_entry import GetCashJournalEntry
from app.core.queries.get_client import GetClient
from app.core.queries.get_company_pnl import GetCompanyPnl
from app.core.queries.get_dashboard_active_rentals import GetDashboardActiveRentals
from app.core.queries.get_dashboard_alerts import GetDashboardAlerts
from app.core.queries.get_dashboard_kpis import GetDashboardKpis
from app.core.queries.get_dashboard_revenue_chart import GetDashboardRevenueChart
from app.core.queries.get_fine import GetFine
from app.core.queries.get_investor import GetInvestor
from app.core.queries.get_investor_pnl import GetInvestorPnl
from app.core.queries.get_mobile_metrics import GetMobileMetrics
from app.core.queries.get_mobile_vehicle import GetMobileVehicle
from app.core.queries.get_my_active_rental import GetMyActiveRental
from app.core.queries.get_my_documents import GetMyDocuments
from app.core.queries.get_my_fines import GetMyFines
from app.core.queries.get_my_outstanding import GetMyOutstanding
from app.core.queries.get_my_payments import GetMyPayments
from app.core.queries.get_my_profile import GetMyProfile
from app.core.queries.get_my_rental import GetMyRental
from app.core.queries.get_my_verification import GetMyVerification
from app.core.queries.get_organization import GetOrganization
from app.core.queries.get_rental import GetRental
from app.core.queries.get_rental_calendar import GetRentalCalendar
from app.core.queries.get_returns_queue import GetReturnsQueue
from app.core.queries.get_service_task import GetServiceTask
from app.core.queries.get_transaction import GetTransaction
from app.core.queries.get_vehicle import GetVehicle
from app.core.queries.get_vehicle_availability import GetVehicleAvailability
from app.core.queries.get_vehicle_financials import GetVehicleFinancials
from app.core.queries.get_vehicle_pricing import GetVehiclePricing
from app.core.queries.get_vehicle_timeline import GetVehicleTimeline
from app.core.queries.get_vehicles_comparison import GetVehiclesComparison
from app.core.queries.investor_portal_dashboard import InvestorPortalDashboard
from app.core.queries.investor_portal_payouts import InvestorPortalPayouts
from app.core.queries.investor_portal_vehicles import InvestorPortalVehicles
from app.core.queries.list_additional_services import ListAdditionalServices
from app.core.queries.list_booking_requests import ListBookingRequests
from app.core.queries.list_branches import ListBranches
from app.core.queries.list_cash_journal_entries import ListCashJournalEntries
from app.core.queries.list_clients import ListClients
from app.core.queries.list_expense_categories import ListExpenseCategories
from app.core.queries.list_fines import ListFines
from app.core.queries.list_investor_payouts import ListInvestorPayouts
from app.core.queries.list_investor_vehicles import ListInvestorVehicles
from app.core.queries.list_investors import ListInvestors
from app.core.queries.list_mobile_vehicles import ListMobileVehicles
from app.core.queries.list_my_notifications import ListMyNotifications
from app.core.queries.list_my_organizations import ListMyOrganizations
from app.core.queries.list_my_rentals import ListMyRentals
from app.core.queries.list_organizations import ListOrganizations
from app.core.queries.list_pending_extensions import ListPendingExtensions
from app.core.queries.list_pending_payments import ListPendingPayments
from app.core.queries.list_rental_services import ListRentalServices
from app.core.queries.list_rentals import ListRentals
from app.core.queries.list_service_tasks import ListServiceTasks
from app.core.queries.list_transactions import ListTransactions
from app.core.queries.list_users import ListUsers
from app.core.queries.list_vehicle_categories import ListVehicleCategories
from app.core.queries.list_vehicle_documents import ListVehicleDocuments
from app.core.queries.list_vehicle_pricing import ListVehiclePricing
from app.core.queries.list_vehicles import ListVehicles
from app.core.queries.ports.additional_service_reader import AdditionalServiceReader
from app.core.queries.ports.branch_reader import BranchReader
from app.core.queries.ports.cash_journal_reader import CashJournalReader
from app.core.queries.ports.client_document_reader import ClientDocumentReader
from app.core.queries.ports.client_organization_reader import ClientOrganizationReader
from app.core.queries.ports.client_reader import ClientReader
from app.core.queries.ports.dashboard_reader import DashboardReader
from app.core.queries.ports.expense_category_reader import ExpenseCategoryReader
from app.core.queries.ports.extension_request_reader import ExtensionRequestReader
from app.core.queries.ports.fine_reader import FineReader
from app.core.queries.ports.investor_reader import InvestorReader
from app.core.queries.ports.mobile_metrics_reader import MobileMetricsReader
from app.core.queries.ports.mobile_rental_reader import MobileRentalReader
from app.core.queries.ports.mobile_vehicle_reader import MobileVehicleReader
from app.core.queries.ports.notification_reader import NotificationReader
from app.core.queries.ports.organization_reader import OrganizationReader
from app.core.queries.ports.rental_calendar_reader import RentalCalendarReader
from app.core.queries.ports.rental_reader import RentalReader
from app.core.queries.ports.rental_service_reader import RentalServiceReader
from app.core.queries.ports.report_reader import ReportReader
from app.core.queries.ports.returns_queue_reader import ReturnsQueueReader
from app.core.queries.ports.service_task_reader import ServiceTaskReader
from app.core.queries.ports.transaction_reader import TransactionReader
from app.core.queries.ports.user_reader import UserReader
from app.core.queries.ports.vehicle_category_reader import VehicleCategoryReader
from app.core.queries.ports.vehicle_document_reader import VehicleDocumentReader
from app.core.queries.ports.vehicle_financials_reader import VehicleFinancialsReader
from app.core.queries.ports.vehicle_pricing_reader import VehiclePricingReader
from app.core.queries.ports.vehicle_reader import VehicleReader
from app.core.queries.ports.vehicle_timeline_reader import VehicleTimelineReader
from app.infrastructure.adapters.auth_session_access_revoker import AuthSessionAccessRevoker
from app.infrastructure.adapters.auth_session_identity_provider import AuthSessionIdentityProvider
from app.infrastructure.adapters.bcrypt_password_hasher import (
    BcryptPasswordHasher,
    HasherSemaphore,
    HasherThreadPoolExecutor,
)
from app.infrastructure.adapters.sqla_additional_service_reader import SqlaAdditionalServiceReader
from app.infrastructure.adapters.sqla_additional_service_tx_storage import SqlaAdditionalServiceTxStorage
from app.infrastructure.adapters.sqla_branch_reader import SqlaBranchReader
from app.infrastructure.adapters.sqla_branch_tx_storage import SqlaBranchTxStorage
from app.infrastructure.adapters.sqla_cash_journal_reader import SqlaCashJournalReader
from app.infrastructure.adapters.sqla_cash_journal_tx_storage import SqlaCashJournalTxStorage
from app.infrastructure.adapters.sqla_client_document_reader import SqlaClientDocumentReader
from app.infrastructure.adapters.sqla_client_organization_reader import SqlaClientOrganizationReader
from app.infrastructure.adapters.sqla_client_organization_tx_storage import SqlaClientOrganizationTxStorage
from app.infrastructure.adapters.sqla_client_reader import SqlaClientReader
from app.infrastructure.adapters.sqla_client_tx_storage import SqlaClientTxStorage
from app.infrastructure.adapters.sqla_dashboard_reader import SqlaDashboardReader
from app.infrastructure.adapters.sqla_device_token_tx_storage import SqlaDeviceTokenTxStorage
from app.infrastructure.adapters.sqla_expense_category_reader import SqlaExpenseCategoryReader
from app.infrastructure.adapters.sqla_expense_category_tx_storage import SqlaExpenseCategoryTxStorage
from app.infrastructure.adapters.sqla_extension_request_reader import SqlaExtensionRequestReader
from app.infrastructure.adapters.sqla_extension_request_tx_storage import SqlaExtensionRequestTxStorage
from app.infrastructure.adapters.sqla_fine_reader import SqlaFineReader
from app.infrastructure.adapters.sqla_fine_tx_storage import SqlaFineTxStorage
from app.infrastructure.adapters.sqla_flusher import SqlaFlusher
from app.infrastructure.adapters.sqla_investor_payout_tx_storage import SqlaInvestorPayoutTxStorage
from app.infrastructure.adapters.sqla_investor_reader import SqlaInvestorReader
from app.infrastructure.adapters.sqla_investor_tx_storage import SqlaInvestorTxStorage
from app.infrastructure.adapters.sqla_mobile_metrics_reader import SqlaMobileMetricsReader
from app.infrastructure.adapters.sqla_mobile_rental_reader import SqlaMobileRentalReader
from app.infrastructure.adapters.sqla_mobile_vehicle_reader import SqlaMobileVehicleReader
from app.infrastructure.adapters.sqla_notification_reader import SqlaNotificationReader
from app.infrastructure.adapters.sqla_notification_tx_storage import SqlaNotificationTxStorage
from app.infrastructure.adapters.sqla_organization_reader import SqlaOrganizationReader
from app.infrastructure.adapters.sqla_organization_tx_storage import SqlaOrganizationTxStorage
from app.infrastructure.adapters.sqla_payment_tx_storage import SqlaPaymentTxStorage
from app.infrastructure.adapters.sqla_rental_calendar_reader import SqlaRentalCalendarReader
from app.infrastructure.adapters.sqla_rental_reader import SqlaRentalReader
from app.infrastructure.adapters.sqla_rental_service_reader import SqlaRentalServiceReader
from app.infrastructure.adapters.sqla_rental_service_tx_storage import SqlaRentalServiceTxStorage
from app.infrastructure.adapters.sqla_rental_tx_storage import SqlaRentalTxStorage
from app.infrastructure.adapters.sqla_report_reader import SqlaReportReader
from app.infrastructure.adapters.sqla_returns_queue_reader import SqlaReturnsQueueReader
from app.infrastructure.adapters.sqla_service_task_reader import SqlaServiceTaskReader
from app.infrastructure.adapters.sqla_service_task_tx_storage import SqlaServiceTaskTxStorage
from app.infrastructure.adapters.sqla_transaction_manager import SqlaTransactionManager
from app.infrastructure.adapters.sqla_transaction_reader import SqlaTransactionReader
from app.infrastructure.adapters.sqla_user_reader import SqlaUserReader
from app.infrastructure.adapters.sqla_user_tx_storage import SqlaUserTxStorage
from app.infrastructure.adapters.sqla_vehicle_category_reader import SqlaVehicleCategoryReader
from app.infrastructure.adapters.sqla_vehicle_category_tx_storage import SqlaVehicleCategoryTxStorage
from app.infrastructure.adapters.sqla_vehicle_document_reader import SqlaVehicleDocumentReader
from app.infrastructure.adapters.sqla_vehicle_document_tx_storage import SqlaVehicleDocumentTxStorage
from app.infrastructure.adapters.sqla_vehicle_financials_reader import SqlaVehicleFinancialsReader
from app.infrastructure.adapters.sqla_vehicle_investor_tx_storage import SqlaVehicleInvestorTxStorage
from app.infrastructure.adapters.sqla_vehicle_pricing_reader import SqlaVehiclePricingReader
from app.infrastructure.adapters.sqla_vehicle_pricing_tx_storage import SqlaVehiclePricingTxStorage
from app.infrastructure.adapters.sqla_vehicle_reader import SqlaVehicleReader
from app.infrastructure.adapters.sqla_vehicle_timeline_reader import SqlaVehicleTimelineReader
from app.infrastructure.adapters.sqla_vehicle_tx_storage import SqlaVehicleTxStorage
from app.infrastructure.adapters.stub_push_sender import StubPushSender
from app.infrastructure.adapters.system_utc_timer import SystemUtcTimer
from app.infrastructure.job_types import JobRunnerSecret
from app.main.config.settings import InternalJobsSettings, PasswordHasherSettings


class CoreProvider(Provider):
    scope = Scope.REQUEST

    # Services
    user_service = provide(UserService, scope=Scope.APP)
    current_user_service = provide(CurrentUserService)

    # Common Ports
    @provide(scope=Scope.APP)
    def provide_password_hasher(
        self,
        settings: PasswordHasherSettings,
        executor: HasherThreadPoolExecutor,
        semaphore: HasherSemaphore,
    ) -> PasswordHasher:
        return BcryptPasswordHasher(
            pepper=settings.PEPPER.encode(),
            work_factor=settings.WORK_FACTOR,
            executor=executor,
            semaphore=semaphore,
            semaphore_wait_timeout_s=settings.SEMAPHORE_WAIT_TIMEOUT_S,
        )

    @provide(scope=Scope.APP)
    def provide_job_runner_secret(self, settings: InternalJobsSettings) -> JobRunnerSecret:
        return JobRunnerSecret(settings.RUNNER_SECRET)

    push_sender = provide(StubPushSender, provides=PushSender)
    notification_service = provide(NotificationService)

    identity_provider = provide(AuthSessionIdentityProvider, provides=IdentityProvider)
    authz_user_finder = provide(SqlaUserTxStorage, provides=AuthzUserFinder)
    access_revoker = provide(AuthSessionAccessRevoker, provides=AccessRevoker)

    # Commands Ports
    utc_timer = provide(SystemUtcTimer, provides=UtcTimer)
    user_tx_storage = provide(SqlaUserTxStorage, provides=UserTxStorage)
    organization_tx_storage = provide(SqlaOrganizationTxStorage, provides=OrganizationTxStorage)
    branch_tx_storage = provide(SqlaBranchTxStorage, provides=BranchTxStorage)
    vehicle_tx_storage = provide(SqlaVehicleTxStorage, provides=VehicleTxStorage)
    client_tx_storage = provide(SqlaClientTxStorage, provides=ClientTxStorage)
    client_org_tx_storage = provide(SqlaClientOrganizationTxStorage, provides=ClientOrganizationTxStorage)
    rental_tx_storage = provide(SqlaRentalTxStorage, provides=RentalTxStorage)
    payment_tx_storage = provide(SqlaPaymentTxStorage, provides=PaymentTxStorage)
    fine_tx_storage = provide(SqlaFineTxStorage, provides=FineTxStorage)
    service_task_tx_storage = provide(SqlaServiceTaskTxStorage, provides=ServiceTaskTxStorage)
    investor_tx_storage = provide(SqlaInvestorTxStorage, provides=InvestorTxStorage)
    vehicle_investor_tx_storage = provide(SqlaVehicleInvestorTxStorage, provides=VehicleInvestorTxStorage)
    investor_payout_tx_storage = provide(SqlaInvestorPayoutTxStorage, provides=InvestorPayoutTxStorage)
    vehicle_pricing_tx_storage = provide(SqlaVehiclePricingTxStorage, provides=VehiclePricingTxStorage)
    vehicle_category_tx_storage = provide(SqlaVehicleCategoryTxStorage, provides=VehicleCategoryTxStorage)
    vehicle_document_tx_storage = provide(SqlaVehicleDocumentTxStorage, provides=VehicleDocumentTxStorage)
    additional_service_tx_storage = provide(SqlaAdditionalServiceTxStorage, provides=AdditionalServiceTxStorage)
    rental_service_tx_storage = provide(SqlaRentalServiceTxStorage, provides=RentalServiceTxStorage)
    expense_category_tx_storage = provide(SqlaExpenseCategoryTxStorage, provides=ExpenseCategoryTxStorage)
    cash_journal_tx_storage = provide(SqlaCashJournalTxStorage, provides=CashJournalTxStorage)
    notification_tx_storage = provide(SqlaNotificationTxStorage, provides=NotificationTxStorage)
    device_token_tx_storage = provide(SqlaDeviceTokenTxStorage, provides=DeviceTokenTxStorage)
    extension_request_tx_storage = provide(SqlaExtensionRequestTxStorage, provides=ExtensionRequestTxStorage)
    flusher = provide(SqlaFlusher, provides=Flusher)
    tx_manager = provide(SqlaTransactionManager, provides=TransactionManager)

    # Commands
    create_user = provide(CreateUser)
    set_user_password = provide(SetUserPassword)
    set_user_role = provide(SetUserRole)
    activate_user = provide(ActivateUser)
    deactivate_user = provide(DeactivateUser)
    create_organization = provide(CreateOrganization)
    create_branch = provide(CreateBranch)
    create_vehicle = provide(CreateVehicle)
    update_vehicle = provide(UpdateVehicle)
    change_vehicle_status = provide(ChangeVehicleStatus)
    create_client = provide(CreateClient)
    update_client = provide(UpdateClient)
    verify_client = provide(VerifyClient)
    blacklist_client = provide(BlacklistClient)
    unblacklist_client = provide(UnblacklistClient)
    create_rental = provide(CreateRental)
    transition_rental = provide(TransitionRental)
    checkin_rental = provide(CheckinRental)
    checkout_rental = provide(CheckoutRental)
    extend_rental = provide(ExtendRental)
    update_rental = provide(UpdateRental)
    approve_booking_request = provide(ApproveBookingRequest)
    reject_booking_request = provide(RejectBookingRequest)
    cancel_rental = provide(CancelRental)
    complete_rental = provide(CompleteRental)
    create_transaction = provide(CreateTransaction)
    update_transaction_status = provide(UpdateTransactionStatus)
    hold_deposit = provide(HoldDeposit)
    release_deposit = provide(ReleaseDeposit)
    charge_client = provide(ChargeClient)
    process_refund = provide(ProcessRefund)
    create_fine = provide(CreateFine)
    charge_fine_to_client = provide(ChargeFineToClient)
    create_service_task = provide(CreateServiceTask)
    update_service_task = provide(UpdateServiceTask)
    complete_service_task = provide(CompleteServiceTask)
    create_investor = provide(CreateInvestor)
    update_investor = provide(UpdateInvestor)
    bind_vehicle_investor = provide(BindVehicleInvestor)
    unbind_vehicle_investor = provide(UnbindVehicleInvestor)
    create_investor_payout = provide(CreateInvestorPayout)
    update_payout_status = provide(UpdatePayoutStatus)
    create_vehicle_pricing = provide(CreateVehiclePricing)
    update_vehicle_pricing = provide(UpdateVehiclePricing)
    create_vehicle_document = provide(CreateVehicleDocument)
    delete_vehicle_document = provide(DeleteVehicleDocument)
    add_vehicle_photo = provide(AddVehiclePhoto)
    remove_vehicle_photo = provide(RemoveVehiclePhoto)
    create_vehicle_category = provide(CreateVehicleCategory)
    update_vehicle_category = provide(UpdateVehicleCategory)
    bulk_change_vehicle_status = provide(BulkChangeVehicleStatus)
    create_additional_service = provide(CreateAdditionalService)
    update_additional_service = provide(UpdateAdditionalService)
    add_rental_service = provide(AddRentalService)
    remove_rental_service = provide(RemoveRentalService)
    update_organization = provide(UpdateOrganization)
    create_expense_category = provide(CreateExpenseCategory)
    update_expense_category = provide(UpdateExpenseCategory)
    create_cash_journal_entry = provide(CreateCashJournalEntry)
    update_cash_journal_entry = provide(UpdateCashJournalEntry)
    confirm_cash_journal_entry = provide(ConfirmCashJournalEntry)
    delete_cash_journal_entry = provide(DeleteCashJournalEntry)

    # Mobile Commands
    register_device_token = provide(RegisterDeviceToken)
    unregister_device_token = provide(UnregisterDeviceToken)
    upload_client_document = provide(UploadClientDocument)
    update_client_profile = provide(UpdateClientProfile)
    mark_notification_read = provide(MarkNotificationRead)
    update_notification_preferences = provide(UpdateNotificationPreferences)
    submit_booking_request = provide(SubmitBookingRequestCommand)
    cancel_own_rental = provide(CancelOwnRental)
    record_client_payment = provide(RecordClientPayment)
    confirm_client_payment = provide(ConfirmClientPayment)
    reject_client_payment = provide(RejectClientPayment)
    submit_extension_request = provide(SubmitExtensionRequestCommand)
    approve_extension_request = provide(ApproveExtensionRequest)
    reject_extension_request = provide(RejectExtensionRequest)
    send_debt_reminder = provide(SendDebtReminder)
    check_pickup_reminders = provide(CheckPickupReminders)
    check_return_reminders = provide(CheckReturnReminders)
    check_overdue_rentals = provide(CheckOverdueRentals)
    join_organization = provide(JoinOrganization)
    leave_organization = provide(LeaveOrganization)

    # Query Ports
    user_reader = provide(SqlaUserReader, provides=UserReader)
    organization_reader = provide(SqlaOrganizationReader, provides=OrganizationReader)
    branch_reader = provide(SqlaBranchReader, provides=BranchReader)
    vehicle_reader = provide(SqlaVehicleReader, provides=VehicleReader)
    client_reader = provide(SqlaClientReader, provides=ClientReader)
    client_org_reader = provide(SqlaClientOrganizationReader, provides=ClientOrganizationReader)
    client_document_reader = provide(SqlaClientDocumentReader, provides=ClientDocumentReader)
    rental_reader = provide(SqlaRentalReader, provides=RentalReader)
    rental_calendar_reader = provide(SqlaRentalCalendarReader, provides=RentalCalendarReader)
    returns_queue_reader = provide(SqlaReturnsQueueReader, provides=ReturnsQueueReader)
    transaction_reader = provide(SqlaTransactionReader, provides=TransactionReader)
    fine_reader = provide(SqlaFineReader, provides=FineReader)
    service_task_reader = provide(SqlaServiceTaskReader, provides=ServiceTaskReader)
    investor_reader = provide(SqlaInvestorReader, provides=InvestorReader)
    vehicle_pricing_reader = provide(SqlaVehiclePricingReader, provides=VehiclePricingReader)
    vehicle_financials_reader = provide(SqlaVehicleFinancialsReader, provides=VehicleFinancialsReader)
    report_reader = provide(SqlaReportReader, provides=ReportReader)
    dashboard_reader = provide(SqlaDashboardReader, provides=DashboardReader)
    vehicle_timeline_reader = provide(SqlaVehicleTimelineReader, provides=VehicleTimelineReader)
    vehicle_category_reader = provide(SqlaVehicleCategoryReader, provides=VehicleCategoryReader)
    vehicle_document_reader = provide(SqlaVehicleDocumentReader, provides=VehicleDocumentReader)
    additional_service_reader = provide(SqlaAdditionalServiceReader, provides=AdditionalServiceReader)
    rental_service_reader = provide(SqlaRentalServiceReader, provides=RentalServiceReader)
    expense_category_reader = provide(SqlaExpenseCategoryReader, provides=ExpenseCategoryReader)
    cash_journal_reader = provide(SqlaCashJournalReader, provides=CashJournalReader)
    notification_reader = provide(SqlaNotificationReader, provides=NotificationReader)
    mobile_vehicle_reader = provide(SqlaMobileVehicleReader, provides=MobileVehicleReader)
    mobile_rental_reader = provide(SqlaMobileRentalReader, provides=MobileRentalReader)
    extension_request_reader = provide(SqlaExtensionRequestReader, provides=ExtensionRequestReader)
    mobile_metrics_reader = provide(SqlaMobileMetricsReader, provides=MobileMetricsReader)

    # Queries
    list_users = provide(ListUsers)
    list_organizations = provide(ListOrganizations)
    get_organization = provide(GetOrganization)
    list_branches = provide(ListBranches)
    list_vehicles = provide(ListVehicles)
    get_vehicle = provide(GetVehicle)
    list_clients = provide(ListClients)
    get_client = provide(GetClient)
    list_rentals = provide(ListRentals)
    get_rental = provide(GetRental)
    get_rental_calendar = provide(GetRentalCalendar)
    get_returns_queue = provide(GetReturnsQueue)
    list_transactions = provide(ListTransactions)
    get_transaction = provide(GetTransaction)
    list_fines = provide(ListFines)
    get_fine = provide(GetFine)
    list_service_tasks = provide(ListServiceTasks)
    get_service_task = provide(GetServiceTask)
    list_investors = provide(ListInvestors)
    get_investor = provide(GetInvestor)
    list_investor_vehicles = provide(ListInvestorVehicles)
    list_investor_payouts = provide(ListInvestorPayouts)
    get_investor_pnl = provide(GetInvestorPnl)
    investor_portal_dashboard = provide(InvestorPortalDashboard)
    investor_portal_vehicles = provide(InvestorPortalVehicles)
    investor_portal_payouts = provide(InvestorPortalPayouts)
    list_vehicle_pricing = provide(ListVehiclePricing)
    get_vehicle_pricing = provide(GetVehiclePricing)
    get_vehicle_financials = provide(GetVehicleFinancials)
    get_vehicle_timeline = provide(GetVehicleTimeline)
    list_vehicle_categories = provide(ListVehicleCategories)
    list_vehicle_documents = provide(ListVehicleDocuments)
    list_additional_services = provide(ListAdditionalServices)
    list_rental_services = provide(ListRentalServices)
    list_expense_categories = provide(ListExpenseCategories)
    list_cash_journal_entries = provide(ListCashJournalEntries)
    get_cash_journal_entry = provide(GetCashJournalEntry)
    get_cash_journal_balance = provide(GetCashJournalBalance)
    get_company_pnl = provide(GetCompanyPnl)
    get_cash_flow = provide(GetCashFlow)
    get_vehicles_comparison = provide(GetVehiclesComparison)
    get_dashboard_kpis = provide(GetDashboardKpis)
    get_dashboard_alerts = provide(GetDashboardAlerts)
    get_dashboard_active_rentals = provide(GetDashboardActiveRentals)
    get_dashboard_revenue_chart = provide(GetDashboardRevenueChart)

    # Mobile Queries
    get_my_profile = provide(GetMyProfile)
    get_my_verification = provide(GetMyVerification)
    list_my_notifications = provide(ListMyNotifications)
    list_mobile_vehicles = provide(ListMobileVehicles)
    get_mobile_vehicle = provide(GetMobileVehicle)
    get_vehicle_availability = provide(GetVehicleAvailability)
    list_my_rentals = provide(ListMyRentals)
    get_my_rental = provide(GetMyRental)
    get_my_active_rental = provide(GetMyActiveRental)
    get_my_fines = provide(GetMyFines)
    get_my_payments = provide(GetMyPayments)
    get_my_outstanding = provide(GetMyOutstanding)
    get_my_documents = provide(GetMyDocuments)
    list_pending_payments = provide(ListPendingPayments)
    list_booking_requests = provide(ListBookingRequests)
    list_pending_extensions = provide(ListPendingExtensions)
    get_mobile_metrics = provide(GetMobileMetrics)
    list_my_organizations = provide(ListMyOrganizations)
