from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.enterprise.entities.report import Report


class ReportsRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        fund_id: str,
        reference_month: datetime,
        publication_date: datetime | None,
        pdf_url: str,
        pdf_hash: str | None,
        status: str,
        error_message: str | None,
    ) -> Report: ...

    @abstractmethod
    async def find_by_id(self, report_id: str) -> Report | None: ...

    @abstractmethod
    async def find_by_fund_id_and_month(self, fund_id: str, reference_month: datetime) -> Report | None: ...

    @abstractmethod
    async def find_by_fund_id(self, fund_id: str) -> list[Report]: ...

    @abstractmethod
    async def find_by_fund_id_in_period(
        self, fund_id: str, period_start: datetime, period_end: datetime
    ) -> list[Report]: ...

    @abstractmethod
    async def update_status(
        self, report_id: str, status: str, error_message: str | None = None
    ) -> Report: ...

    @abstractmethod
    async def update_pdf_hash(self, report_id: str, pdf_hash: str) -> Report: ...
