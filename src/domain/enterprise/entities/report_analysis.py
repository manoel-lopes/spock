from typing import Any

from src.core.domain.entity import Entity


class ReportAnalysis(Entity):
    report_id: str
    algorithm_version: str
    detected_metrics: dict[str, Any]
    weights: dict[str, Any]
    quality_score: float
