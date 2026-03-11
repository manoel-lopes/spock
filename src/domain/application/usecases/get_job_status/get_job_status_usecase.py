from dataclasses import dataclass

from src.domain.application.repositories.processing_jobs_repository import ProcessingJobsRepository
from src.domain.enterprise.entities.processing_job import ProcessingJob
from src.shared.application.errors.resource_not_found import ResourceNotFoundError


@dataclass
class GetJobStatusRequest:
    job_id: str


class GetJobStatusUseCase:
    def __init__(
        self,
        processing_jobs_repository: ProcessingJobsRepository,
    ) -> None:
        self._processing_jobs_repository = processing_jobs_repository

    async def execute(self, req: GetJobStatusRequest) -> ProcessingJob:
        job = await self._processing_jobs_repository.find_by_external_job_id(req.job_id)
        if not job:
            raise ResourceNotFoundError("Job")
        return job
