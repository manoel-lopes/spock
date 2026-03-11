from datetime import datetime
from typing import Any

from src.core.domain.entity import Entity


class IncidentReport(Entity):
    fund_id: str
    type: str
    severity: str
    title: str
    description: str
    resolved_at: datetime | None = None
    metadata: dict[str, Any] | None = None
