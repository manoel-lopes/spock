from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    detected_metrics: dict[str, bool]
    weights: dict[str, float]
    quality_score: float


class TransparencyAnalyzer(ABC):
    @abstractmethod
    def analyze(self, text: str) -> AnalysisResult: ...

    @abstractmethod
    def get_version(self) -> str: ...
