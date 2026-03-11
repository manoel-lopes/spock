from abc import ABC, abstractmethod
from typing import Any

from src.domain.enterprise.entities.report_analysis import ReportAnalysis


class ReportAnalysesRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        report_id: str,
        algorithm_version: str,
        detected_metrics: dict[str, Any],
        weights: dict[str, Any],
        quality_score: float,
    ) -> ReportAnalysis: ...

    @abstractmethod
    async def find_by_report_ids(self, report_ids: list[str]) -> list[ReportAnalysis]: ...

    @abstractmethod
    async def find_by_report_id_and_version(
        self, report_id: str, algorithm_version: str
    ) -> ReportAnalysis | None: ...
