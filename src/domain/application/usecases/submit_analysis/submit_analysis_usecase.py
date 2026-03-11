import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

from src.domain.application.repositories.funds_repository import FundsRepository
from src.domain.application.repositories.processing_jobs_repository import ProcessingJobsRepository
from src.domain.application.repositories.reports_repository import ReportsRepository
from src.domain.application.usecases.submit_analysis.errors.duplicate_job import DuplicateJobError
from src.infra.queue.ports.job_queue import JobQueue
from src.shared.application.errors.resource_not_found import ResourceNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class SubmitAnalysisRequest:
    ticker: str
    pdf_url: str
    reference_month: datetime
    publication_date: datetime | None = None


@dataclass
class SubmitAnalysisResponse:
    job_id: str
    report_id: str


class SubmitAnalysisUseCase:
    def __init__(
        self,
        funds_repository: FundsRepository,
        reports_repository: ReportsRepository,
        processing_jobs_repository: ProcessingJobsRepository,
        job_queue: JobQueue,
    ) -> None:
        self._funds_repository = funds_repository
        self._reports_repository = reports_repository
        self._processing_jobs_repository = processing_jobs_repository
        self._job_queue = job_queue

    async def execute(self, req: SubmitAnalysisRequest) -> SubmitAnalysisResponse:
        fund = await self._funds_repository.find_by_ticker(req.ticker)
        if not fund:
            raise ResourceNotFoundError("Fund")

        payload = {
            "fundId": fund.id,
            "pdfUrl": req.pdf_url,
            "referenceMonth": req.reference_month.isoformat(),
        }

        existing_job = await self._processing_jobs_repository.find_pending_by_payload(
            "report-analysis", payload
        )
        if existing_job:
            raise DuplicateJobError()

        report = await self._reports_repository.create(
            fund_id=fund.id,
            reference_month=req.reference_month,
            publication_date=req.publication_date,
            pdf_url=req.pdf_url,
            pdf_hash=None,
            status="pending",
            error_message=None,
        )

        processing_job = await self._processing_jobs_repository.create(
            external_job_id=f"pending-{uuid.uuid4()}",
            type="report-analysis",
            payload=payload,
            status="pending",
            attempts=0,
            started_at=None,
            completed_at=None,
            error_message=None,
        )

        external_job_id = await self._job_queue.add(
            "report-analysis",
            {
                "processingJobId": processing_job.id,
                "reportId": report.id,
                "pdfUrl": req.pdf_url,
            },
        )

        await self._processing_jobs_repository.update_external_job_id(
            processing_job.id, external_job_id
        )

        return SubmitAnalysisResponse(job_id=external_job_id, report_id=report.id)
