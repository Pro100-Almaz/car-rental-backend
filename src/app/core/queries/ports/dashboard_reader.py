from abc import abstractmethod
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from app.core.queries.models.dashboard_active_rentals import DashboardActiveRentalsQm
from app.core.queries.models.dashboard_alerts import DashboardAlertsQm
from app.core.queries.models.dashboard_kpis import DashboardKpisQm
from app.core.queries.models.dashboard_revenue_chart import DashboardRevenueChartQm


class DashboardReader(Protocol):
    @abstractmethod
    async def get_kpis(
        self,
        *,
        organization_id: UUID,
        date_from: date,
        date_to: date,
        prev_date_from: date,
        prev_date_to: date,
        now: datetime,
    ) -> DashboardKpisQm: ...

    @abstractmethod
    async def get_alerts(
        self,
        *,
        organization_id: UUID,
        now: datetime,
    ) -> DashboardAlertsQm: ...

    @abstractmethod
    async def get_active_rentals(
        self,
        *,
        organization_id: UUID,
        limit: int,
        now: datetime,
    ) -> DashboardActiveRentalsQm: ...

    @abstractmethod
    async def get_revenue_chart(
        self,
        *,
        organization_id: UUID,
        date_from: date,
        date_to: date,
    ) -> DashboardRevenueChartQm: ...
