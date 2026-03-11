import asyncio
from dataclasses import dataclass

from src.domain.application.repositories.report_analyses_repository import ReportAnalysesRepository
from src.domain.application.repositories.report_contents_repository import ReportContentsRepository
from src.domain.application.repositories.reports_repository import ReportsRepository
from src.domain.enterprise.entities.report import Report
from src.domain.enterprise.entities.report_analysis import ReportAnalysis
from src.domain.enterprise.entities.report_content import ReportContent
from src.shared.application.errors.resource_not_found import ResourceNotFoundError


@dataclass
class GetAnalysisResultRequest:
    report_id: str


@dataclass
class GetAnalysisResultResponse:
    report: Report
    content: ReportContent | None
    analysis: ReportAnalysis | None


class GetAnalysisResultUseCase:
    def __init__(
        self,
        reports_repository: ReportsRepository,
        report_contents_repository: ReportContentsRepository,
        report_analyses_repository: ReportAnalysesRepository,
    ) -> None:
        self._reports_repository = reports_repository
        self._report_contents_repository = report_contents_repository
        self._report_analyses_repository = report_analyses_repository

    async def execute(self, req: GetAnalysisResultRequest) -> GetAnalysisResultResponse:
        report = await self._reports_repository.find_by_id(req.report_id)
        if not report:
            raise ResourceNotFoundError("Report")

        content, analysis = await asyncio.gather(
            self._report_contents_repository.find_by_report_id(req.report_id),
            self._report_analyses_repository.find_by_report_id_and_version(req.report_id, "1.0.0"),
        )

        return GetAnalysisResultResponse(
            report=report,
            content=content,
            analysis=analysis,
        )
