from abc import abstractmethod
from datetime import date
from typing import Protocol
from uuid import UUID

from app.core.queries.models.report_cash_flow import CashFlowQm
from app.core.queries.models.report_pnl import CompanyPnlQm
from app.core.queries.models.report_vehicles_comparison import VehiclesComparisonQm


class ReportReader(Protocol):
    @abstractmethod
    async def get_company_pnl(
        self,
        *,
        organization_id: UUID,
        date_from: date,
        date_to: date,
    ) -> CompanyPnlQm: ...

    @abstractmethod
    async def get_cash_flow(
        self,
        *,
        organization_id: UUID,
        date_from: date,
        date_to: date,
    ) -> CashFlowQm: ...

    @abstractmethod
    async def get_vehicles_comparison(
        self,
        *,
        organization_id: UUID,
        date_from: date,
        date_to: date,
    ) -> VehiclesComparisonQm: ...
