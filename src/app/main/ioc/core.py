from dishka import Provider, Scope, provide

from app.core.commands.activate_user import ActivateUser
from app.core.commands.add_rental_service import AddRentalService
from app.core.commands.bind_vehicle_investor import BindVehicleInvestor
from app.core.commands.blacklist_client import BlacklistClient
from app.core.commands.cancel_rental import CancelRental
from app.core.commands.change_vehicle_status import ChangeVehicleStatus
from app.core.commands.charge_client import ChargeClient
from app.core.commands.charge_fine_to_client import ChargeFineToClient
from app.core.commands.checkin_rental import CheckinRental
from app.core.commands.checkout_rental import CheckoutRental
from app.core.commands.complete_rental import CompleteRental
from app.core.commands.complete_service_task import CompleteServiceTask
from app.core.commands.confirm_cash_journal_entry import ConfirmCashJournalEntry
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
from app.core.commands.create_vehicle_pricing import CreateVehiclePricing
from app.core.commands.deactivate_user import DeactivateUser
from app.core.commands.extend_rental import ExtendRental
from app.core.commands.hold_deposit import HoldDeposit
from app.core.commands.ports.additional_service_tx_storage import AdditionalServiceTxStorage
from app.core.commands.ports.branch_tx_storage import BranchTxStorage
from app.core.commands.ports.cash_journal_tx_storage import CashJournalTxStorage
from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.commands.ports.expense_category_tx_storage import ExpenseCategoryTxStorage
from app.core.commands.ports.fine_tx_storage import FineTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.investor_payout_tx_storage import InvestorPayoutTxStorage
from app.core.commands.ports.investor_tx_storage import InvestorTxStorage
from app.core.commands.ports.organization_tx_storage import OrganizationTxStorage
from app.core.commands.ports.payment_tx_storage import PaymentTxStorage
from app.core.commands.ports.rental_service_tx_storage import RentalServiceTxStorage
from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.commands.ports.service_task_tx_storage import ServiceTaskTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.user_tx_storage import UserTxStorage
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.ports.vehicle_investor_tx_storage import VehicleInvestorTxStorage
from app.core.commands.ports.vehicle_pricing_tx_storage import VehiclePricingTxStorage
from app.core.commands.ports.vehicle_tx_storage import VehicleTxStorage
from app.core.commands.process_refund import ProcessRefund
from app.core.commands.release_deposit import ReleaseDeposit
from app.core.commands.remove_rental_service import RemoveRentalService
from app.core.commands.set_user_password import SetUserPassword
from app.core.commands.set_user_role import SetUserRole
from app.core.commands.transition_rental import TransitionRental
from app.core.commands.unbind_vehicle_investor import UnbindVehicleInvestor
from app.core.commands.update_additional_service import UpdateAdditionalService
from app.core.commands.update_cash_journal_entry import UpdateCashJournalEntry
from app.core.commands.update_client import UpdateClient
from app.core.commands.update_expense_category import UpdateExpenseCategory
from app.core.commands.update_investor import UpdateInvestor
from app.core.commands.update_payout_status import UpdatePayoutStatus
from app.core.commands.update_service_task import UpdateServiceTask
from app.core.commands.update_transaction_status import UpdateTransactionStatus
from app.core.commands.update_vehicle import UpdateVehicle
from app.core.commands.update_vehicle_pricing import UpdateVehiclePricing
from app.core.commands.verify_client import VerifyClient
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.ports import AuthzUserFinder
from app.core.common.ports.access_revoker import AccessRevoker
from app.core.common.ports.identity_provider import IdentityProvider
from app.core.common.ports.password_hasher import PasswordHasher
from app.core.common.services.user import UserService
from app.core.queries.get_cash_journal_balance import GetCashJournalBalance
from app.core.queries.get_cash_journal_entry import GetCashJournalEntry
from app.core.queries.get_client import GetClient
from app.core.queries.get_fine import GetFine
from app.core.queries.get_investor import GetInvestor
from app.core.queries.get_rental import GetRental
from app.core.queries.get_service_task import GetServiceTask
from app.core.queries.get_transaction import GetTransaction
from app.core.queries.get_vehicle import GetVehicle
from app.core.commands.bulk_change_vehicle_status import BulkChangeVehicleStatus
from app.core.commands.create_vehicle_category import CreateVehicleCategory
from app.core.commands.create_vehicle_document import CreateVehicleDocument
from app.core.commands.delete_vehicle_document import DeleteVehicleDocument
from app.core.commands.manage_vehicle_photos import AddVehiclePhoto, RemoveVehiclePhoto
from app.core.commands.update_vehicle_category import UpdateVehicleCategory
from app.core.commands.ports.vehicle_category_tx_storage import VehicleCategoryTxStorage
from app.core.queries.list_vehicle_categories import ListVehicleCategories
from app.core.queries.ports.vehicle_category_reader import VehicleCategoryReader
from app.core.queries.get_vehicle_financials import GetVehicleFinancials
from app.core.queries.get_vehicle_pricing import GetVehiclePricing
from app.core.queries.get_vehicle_timeline import GetVehicleTimeline
from app.core.queries.list_vehicle_documents import ListVehicleDocuments
from app.core.queries.list_additional_services import ListAdditionalServices
from app.core.queries.list_branches import ListBranches
from app.core.queries.list_cash_journal_entries import ListCashJournalEntries
from app.core.queries.list_clients import ListClients
from app.core.queries.list_expense_categories import ListExpenseCategories
from app.core.queries.list_fines import ListFines
from app.core.queries.list_investor_payouts import ListInvestorPayouts
from app.core.queries.list_investor_vehicles import ListInvestorVehicles
from app.core.queries.list_investors import ListInvestors
from app.core.queries.list_organizations import ListOrganizations
from app.core.queries.list_rental_services import ListRentalServices
from app.core.queries.list_rentals import ListRentals
from app.core.queries.list_service_tasks import ListServiceTasks
from app.core.queries.list_transactions import ListTransactions
from app.core.queries.list_users import ListUsers
from app.core.queries.list_vehicle_pricing import ListVehiclePricing
from app.core.queries.list_vehicles import ListVehicles
from app.core.queries.ports.additional_service_reader import AdditionalServiceReader
from app.core.queries.ports.branch_reader import BranchReader
from app.core.queries.ports.cash_journal_reader import CashJournalReader
from app.core.queries.ports.client_reader import ClientReader
from app.core.queries.ports.expense_category_reader import ExpenseCategoryReader
from app.core.queries.ports.fine_reader import FineReader
from app.core.queries.ports.investor_reader import InvestorReader
from app.core.queries.ports.organization_reader import OrganizationReader
from app.core.queries.ports.rental_reader import RentalReader
from app.core.queries.ports.rental_service_reader import RentalServiceReader
from app.core.queries.ports.service_task_reader import ServiceTaskReader
from app.core.queries.ports.transaction_reader import TransactionReader
from app.core.queries.ports.user_reader import UserReader
from app.core.queries.ports.vehicle_pricing_reader import VehiclePricingReader
from app.core.commands.ports.vehicle_document_tx_storage import VehicleDocumentTxStorage
from app.core.queries.ports.vehicle_document_reader import VehicleDocumentReader
from app.core.queries.ports.vehicle_financials_reader import VehicleFinancialsReader
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
from app.infrastructure.adapters.sqla_client_reader import SqlaClientReader
from app.infrastructure.adapters.sqla_client_tx_storage import SqlaClientTxStorage
from app.infrastructure.adapters.sqla_expense_category_reader import SqlaExpenseCategoryReader
from app.infrastructure.adapters.sqla_expense_category_tx_storage import SqlaExpenseCategoryTxStorage
from app.infrastructure.adapters.sqla_fine_reader import SqlaFineReader
from app.infrastructure.adapters.sqla_fine_tx_storage import SqlaFineTxStorage
from app.infrastructure.adapters.sqla_flusher import SqlaFlusher
from app.infrastructure.adapters.sqla_investor_payout_tx_storage import SqlaInvestorPayoutTxStorage
from app.infrastructure.adapters.sqla_investor_reader import SqlaInvestorReader
from app.infrastructure.adapters.sqla_investor_tx_storage import SqlaInvestorTxStorage
from app.infrastructure.adapters.sqla_organization_reader import SqlaOrganizationReader
from app.infrastructure.adapters.sqla_organization_tx_storage import SqlaOrganizationTxStorage
from app.infrastructure.adapters.sqla_payment_tx_storage import SqlaPaymentTxStorage
from app.infrastructure.adapters.sqla_rental_reader import SqlaRentalReader
from app.infrastructure.adapters.sqla_rental_service_reader import SqlaRentalServiceReader
from app.infrastructure.adapters.sqla_rental_service_tx_storage import SqlaRentalServiceTxStorage
from app.infrastructure.adapters.sqla_rental_tx_storage import SqlaRentalTxStorage
from app.infrastructure.adapters.sqla_service_task_reader import SqlaServiceTaskReader
from app.infrastructure.adapters.sqla_service_task_tx_storage import SqlaServiceTaskTxStorage
from app.infrastructure.adapters.sqla_transaction_manager import SqlaTransactionManager
from app.infrastructure.adapters.sqla_transaction_reader import SqlaTransactionReader
from app.infrastructure.adapters.sqla_user_reader import SqlaUserReader
from app.infrastructure.adapters.sqla_user_tx_storage import SqlaUserTxStorage
from app.infrastructure.adapters.sqla_vehicle_investor_tx_storage import SqlaVehicleInvestorTxStorage
from app.infrastructure.adapters.sqla_vehicle_pricing_reader import SqlaVehiclePricingReader
from app.infrastructure.adapters.sqla_vehicle_pricing_tx_storage import SqlaVehiclePricingTxStorage
from app.infrastructure.adapters.sqla_vehicle_category_reader import SqlaVehicleCategoryReader
from app.infrastructure.adapters.sqla_vehicle_category_tx_storage import SqlaVehicleCategoryTxStorage
from app.infrastructure.adapters.sqla_vehicle_document_reader import SqlaVehicleDocumentReader
from app.infrastructure.adapters.sqla_vehicle_document_tx_storage import SqlaVehicleDocumentTxStorage
from app.infrastructure.adapters.sqla_vehicle_financials_reader import SqlaVehicleFinancialsReader
from app.infrastructure.adapters.sqla_vehicle_reader import SqlaVehicleReader
from app.infrastructure.adapters.sqla_vehicle_timeline_reader import SqlaVehicleTimelineReader
from app.infrastructure.adapters.sqla_vehicle_tx_storage import SqlaVehicleTxStorage
from app.infrastructure.adapters.system_utc_timer import SystemUtcTimer
from app.main.config.settings import PasswordHasherSettings


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
    create_rental = provide(CreateRental)
    transition_rental = provide(TransitionRental)
    checkin_rental = provide(CheckinRental)
    checkout_rental = provide(CheckoutRental)
    extend_rental = provide(ExtendRental)
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
    create_expense_category = provide(CreateExpenseCategory)
    update_expense_category = provide(UpdateExpenseCategory)
    create_cash_journal_entry = provide(CreateCashJournalEntry)
    update_cash_journal_entry = provide(UpdateCashJournalEntry)
    confirm_cash_journal_entry = provide(ConfirmCashJournalEntry)

    # Query Ports
    user_reader = provide(SqlaUserReader, provides=UserReader)
    organization_reader = provide(SqlaOrganizationReader, provides=OrganizationReader)
    branch_reader = provide(SqlaBranchReader, provides=BranchReader)
    vehicle_reader = provide(SqlaVehicleReader, provides=VehicleReader)
    client_reader = provide(SqlaClientReader, provides=ClientReader)
    rental_reader = provide(SqlaRentalReader, provides=RentalReader)
    transaction_reader = provide(SqlaTransactionReader, provides=TransactionReader)
    fine_reader = provide(SqlaFineReader, provides=FineReader)
    service_task_reader = provide(SqlaServiceTaskReader, provides=ServiceTaskReader)
    investor_reader = provide(SqlaInvestorReader, provides=InvestorReader)
    vehicle_pricing_reader = provide(SqlaVehiclePricingReader, provides=VehiclePricingReader)
    vehicle_financials_reader = provide(SqlaVehicleFinancialsReader, provides=VehicleFinancialsReader)
    vehicle_timeline_reader = provide(SqlaVehicleTimelineReader, provides=VehicleTimelineReader)
    vehicle_category_reader = provide(SqlaVehicleCategoryReader, provides=VehicleCategoryReader)
    vehicle_document_reader = provide(SqlaVehicleDocumentReader, provides=VehicleDocumentReader)
    additional_service_reader = provide(SqlaAdditionalServiceReader, provides=AdditionalServiceReader)
    rental_service_reader = provide(SqlaRentalServiceReader, provides=RentalServiceReader)
    expense_category_reader = provide(SqlaExpenseCategoryReader, provides=ExpenseCategoryReader)
    cash_journal_reader = provide(SqlaCashJournalReader, provides=CashJournalReader)

    # Queries
    list_users = provide(ListUsers)
    list_organizations = provide(ListOrganizations)
    list_branches = provide(ListBranches)
    list_vehicles = provide(ListVehicles)
    get_vehicle = provide(GetVehicle)
    list_clients = provide(ListClients)
    get_client = provide(GetClient)
    list_rentals = provide(ListRentals)
    get_rental = provide(GetRental)
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
