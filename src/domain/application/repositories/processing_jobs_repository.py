from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from src.domain.enterprise.entities.processing_job import ProcessingJob


class ProcessingJobsRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        external_job_id: str,
        type: str,
        payload: dict[str, Any],
        status: str,
        attempts: int,
        started_at: datetime | None,
        completed_at: datetime | None,
        error_message: str | None,
    ) -> ProcessingJob: ...

    @abstractmethod
    async def find_by_external_job_id(self, external_job_id: str) -> ProcessingJob | None: ...

    @abstractmethod
    async def update_status(
        self,
        job_id: str,
        status: str,
        *,
        error_message: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        attempts: int | None = None,
    ) -> ProcessingJob: ...

    @abstractmethod
    async def find_pending_by_payload(
        self, type: str, payload: dict[str, Any]
    ) -> ProcessingJob | None: ...

    @abstractmethod
    async def update_external_job_id(
        self, job_id: str, external_job_id: str
    ) -> ProcessingJob: ...
