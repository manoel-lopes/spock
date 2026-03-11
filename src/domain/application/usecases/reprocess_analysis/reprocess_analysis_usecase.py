from dataclasses import dataclass

from src.domain.application.repositories.processing_jobs_repository import ProcessingJobsRepository
from src.domain.application.repositories.reports_repository import ReportsRepository
from src.infra.queue.ports.job_queue import JobQueue
from src.shared.application.errors.resource_not_found import ResourceNotFoundError


@dataclass
class ReprocessAnalysisRequest:
    report_id: str


@dataclass
class ReprocessAnalysisResponse:
    job_id: str


class ReprocessAnalysisUseCase:
    def __init__(
        self,
        reports_repository: ReportsRepository,
        processing_jobs_repository: ProcessingJobsRepository,
        job_queue: JobQueue,
    ) -> None:
        self._reports_repository = reports_repository
        self._processing_jobs_repository = processing_jobs_repository
        self._job_queue = job_queue

    async def execute(self, req: ReprocessAnalysisRequest) -> ReprocessAnalysisResponse:
        report = await self._reports_repository.find_by_id(req.report_id)
        if not report:
            raise ResourceNotFoundError("Report")

        await self._reports_repository.update_status(req.report_id, "pending")

        external_job_id = await self._job_queue.add(
            "report-analysis",
            {
                "reportId": report.id,
                "pdfUrl": report.pdf_url,
                "forceRedownload": True,
            },
        )

        await self._processing_jobs_repository.create(
            external_job_id=external_job_id,
            type="report-analysis",
            payload={"reportId": report.id, "pdfUrl": report.pdf_url},
            status="pending",
            attempts=0,
            started_at=None,
            completed_at=None,
            error_message=None,
        )

        return ReprocessAnalysisResponse(job_id=external_job_id)
