from dataclasses import dataclass

from src.shared.infra.adapters.analysis.ports.transparency_analyzer import (
    AnalysisResult,
    TransparencyAnalyzer,
)


@dataclass
class MetricDefinition:
    key: str
    keywords: list[str]


EQUITY_METRICS: list[MetricDefinition] = [
    MetricDefinition(key="vacancia_fisica", keywords=["vacância física", "taxa de vacância"]),
    MetricDefinition(key="vacancia_financeira", keywords=["vacância financeira"]),
    MetricDefinition(key="walt", keywords=["walt", "prazo médio dos contratos"]),
    MetricDefinition(key="inquilinos", keywords=["inquilinos", "locatários", "concentração"]),
    MetricDefinition(key="ativos_imoveis", keywords=["carteira", "portfólio", "imóveis", "ativos"]),
    MetricDefinition(key="inadimplencia", keywords=["inadimplência", "inadimplencia"]),
    MetricDefinition(key="cap_rate", keywords=["cap rate", "capitalização"]),
    MetricDefinition(key="pipeline", keywords=["pipeline", "aquisição", "desinvestimento"]),
    MetricDefinition(key="divida_alavancagem", keywords=["dívida", "endividamento", "alavancagem", "amortização"]),
    MetricDefinition(key="comentario_gerencial", keywords=["perspectiva", "comentário", "análise gerencial"]),
]

ALGORITHM_VERSION = "1.0.0"


class EquityTransparencyAnalyzer(TransparencyAnalyzer):
    def analyze(self, text: str) -> AnalysisResult:
        normalized_text = text.lower()
        detected_metrics: dict[str, bool] = {}
        weights: dict[str, float] = {}

        for metric in EQUITY_METRICS:
            found = any(kw in normalized_text for kw in metric.keywords)
            detected_metrics[metric.key] = found
            weights[metric.key] = 1.0 if found else 0.0

        total_score = sum(weights.values())
        quality_score = total_score / len(EQUITY_METRICS)

        return AnalysisResult(
            detected_metrics=detected_metrics,
            weights=weights,
            quality_score=quality_score,
        )

    def get_version(self) -> str:
        return ALGORITHM_VERSION
