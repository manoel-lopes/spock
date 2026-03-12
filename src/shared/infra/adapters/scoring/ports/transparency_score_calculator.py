from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from src.shared.domain.enterprise.entities.report import Report
from src.shared.domain.enterprise.entities.report_analysis import ReportAnalysis


@dataclass
class TransparencyScoreInput:
    reports: list[Report]
    analyses: list[ReportAnalysis]
    period_start: datetime
    period_end: datetime


@dataclass
class TransparencyScoreMetadata:
    report_count: int
    expected_reports: int
    avg_delay_days: float
    avg_quality_score: float


@dataclass
class TransparencyScoreResult:
    regularity: float
    timeliness: float
    quality: float
    final_score: float
    classification: str
    metadata: TransparencyScoreMetadata


class TransparencyScoreCalculator(ABC):
    @abstractmethod
    def calculate(self, input: TransparencyScoreInput) -> TransparencyScoreResult: ...
