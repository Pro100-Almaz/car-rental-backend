"""
Ensures imperative SQLAlchemy mappings are initialized at application startup.

### Purpose:
In Clean Architecture, domain entities remain agnostic of database
mappings. To integrate with SQLAlchemy, mappings must be explicitly
triggered to link ORM attributes to domain classes. Without this setup,
attempts to interact with unmapped entities in database operations
will lead to runtime errors.

### Solution:
This module provides a single entry point to initialize the mapping
of domain entities to database tables. By calling the `map_tables` function,
ORM attributes are linked to domain classes without altering domain code
or introducing infrastructure concerns.

### Usage:
Call the `map_tables` function in the application factory to initialize
mappings at startup. Additionally, it is necessary to call this function
in `env.py` for Alembic migrations to ensure all models are available
during database migrations.
"""

from app.infrastructure.persistence_sqla.mappings.additional_service import map_additional_services_table
from app.infrastructure.persistence_sqla.mappings.auth_session import map_auth_sessions_table
from app.infrastructure.persistence_sqla.mappings.branch import map_branches_table
from app.infrastructure.persistence_sqla.mappings.cash_journal_entry import map_cash_journal_table
from app.infrastructure.persistence_sqla.mappings.client import map_clients_table
from app.infrastructure.persistence_sqla.mappings.email_verification_code import map_email_verification_codes_table
from app.infrastructure.persistence_sqla.mappings.expense_category import map_expense_categories_table
from app.infrastructure.persistence_sqla.mappings.fine import map_fines_table
from app.infrastructure.persistence_sqla.mappings.invite import map_invites_table
from app.infrastructure.persistence_sqla.mappings.investor import map_investors_table
from app.infrastructure.persistence_sqla.mappings.investor_payout import map_investor_payouts_table
from app.infrastructure.persistence_sqla.mappings.organization import map_organizations_table
from app.infrastructure.persistence_sqla.mappings.rental import map_rentals_table
from app.infrastructure.persistence_sqla.mappings.rental_service import map_rental_services_table
from app.infrastructure.persistence_sqla.mappings.service_task import map_service_tasks_table
from app.infrastructure.persistence_sqla.mappings.transaction import map_transactions_table
from app.infrastructure.persistence_sqla.mappings.user import map_users_table
from app.infrastructure.persistence_sqla.mappings.vehicle import map_vehicles_table
from app.infrastructure.persistence_sqla.mappings.vehicle_investor import map_vehicle_investors_table
from app.infrastructure.persistence_sqla.mappings.vehicle_pricing import map_vehicle_pricing_table
from app.infrastructure.persistence_sqla.registry import mapper_registry


def map_tables() -> None:
    if mapper_registry.mappers:
        return
    map_organizations_table()
    map_branches_table()
    map_users_table()
    map_vehicles_table()
    map_clients_table()
    map_rentals_table()
    map_transactions_table()
    map_fines_table()
    map_service_tasks_table()
    map_investors_table()
    map_vehicle_investors_table()
    map_investor_payouts_table()
    map_vehicle_pricing_table()
    map_additional_services_table()
    map_rental_services_table()
    map_expense_categories_table()
    map_cash_journal_table()
    map_auth_sessions_table()
    map_email_verification_codes_table()
    map_invites_table()
