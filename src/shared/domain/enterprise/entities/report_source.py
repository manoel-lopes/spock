from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ReportSource(BaseModel):
    """ReportSource does NOT extend Entity — no updatedAt."""

    id: str
    report_id: str
    source_type: str
    source_url: str
    discovered_at: datetime
    reliability: float = 1.0
    metadata: dict[str, Any] | None = None
    created_at: datetime
