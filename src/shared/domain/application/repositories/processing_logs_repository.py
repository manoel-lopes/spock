from abc import ABC, abstractmethod
from typing import Any

from src.shared.domain.enterprise.entities.processing_log import ProcessingLog


class ProcessingLogsRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        processing_job_id: str,
        stage: str,
        status: str,
        duration_ms: int | None,
        metadata: dict[str, Any] | None,
    ) -> ProcessingLog: ...

    @abstractmethod
    async def find_by_job_id(self, processing_job_id: str) -> list[ProcessingLog]: ...
