from datetime import datetime
from typing import Any

from src.core.domain.entity import Entity


class ProcessingJob(Entity):
    external_job_id: str
    type: str
    payload: dict[str, Any]
    status: str = "pending"
    attempts: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
