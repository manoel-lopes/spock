from datetime import datetime
from typing import Any

from src.shared.core.domain.entity import Entity


class TransparencyScore(Entity):
    fund_id: str
    period_start: datetime
    period_end: datetime
    regularity: float
    timeliness: float
    quality: float
    final_score: float
    classification: str
    algorithm_version: str
    metadata: dict[str, Any] | None = None
