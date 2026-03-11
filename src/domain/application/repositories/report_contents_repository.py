from abc import ABC, abstractmethod

from src.domain.enterprise.entities.report_content import ReportContent


class ReportContentsRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        report_id: str,
        raw_text: str,
        normalized_text: str | None,
        page_count: int,
        parser_version: str | None,
    ) -> ReportContent: ...

    @abstractmethod
    async def find_by_report_id(self, report_id: str) -> ReportContent | None: ...
