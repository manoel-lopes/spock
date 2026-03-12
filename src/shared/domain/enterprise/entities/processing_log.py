from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ProcessingLog(BaseModel):
    """ProcessingLog does NOT extend Entity — no updatedAt."""

    id: str
    processing_job_id: str
    stage: str
    status: str
    duration_ms: int | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
