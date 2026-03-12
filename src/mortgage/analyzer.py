from dataclasses import dataclass

from src.shared.infra.adapters.analysis.ports.transparency_analyzer import (
    AnalysisResult,
    TransparencyAnalyzer,
)


@dataclass
class MetricDefinition:
    key: str
    keywords: list[str]


MORTGAGE_METRICS: list[MetricDefinition] = [
    MetricDefinition(
        key="cri_ratings",
        keywords=["rating", "classificação de risco", "operações de cri"],
    ),
    MetricDefinition(
        key="portfolio_movements",
        keywords=["movimentação da carteira", "aquisição de cri", "venda de cri"],
    ),
    MetricDefinition(
        key="stratified_dre",
        keywords=["dre", "demonstração de resultado", "receitas", "despesas", "não recorrente"],
    ),
    MetricDefinition(
        key="accumulated_periods",
        keywords=["acumulado", "12 meses", "year to date", "últimos 12"],
    ),
    MetricDefinition(
        key="cost_of_leverage",
        keywords=["custo de alavancagem", "custo da dívida", "cdi +", "ipca +"],
    ),
    MetricDefinition(
        key="fii_book",
        keywords=["book de fiis", "posição em fiis", "cotas de fii", "preço médio"],
    ),
    MetricDefinition(
        key="sector_diversification",
        keywords=["diversificação setorial", "securitizadora", "concentração por setor"],
    ),
    MetricDefinition(
        key="accumulated_reserves",
        keywords=["reserva acumulada", "resultado acumulado", "reserva de contingência"],
    ),
    MetricDefinition(
        key="pdd_cris",
        keywords=["pdd", "provisão para devedores duvidosos", "inadimplência de cri"],
    ),
    MetricDefinition(
        key="dividend_guidance",
        keywords=["distribuição de rendimento", "dividendo", "guidance", "projeção de dividendo"],
    ),
    MetricDefinition(
        key="nonperforming_comments",
        keywords=["inadimplência", "reestruturação", "renegociação", "default", "não performado"],
    ),
    MetricDefinition(
        key="grace_period",
        keywords=["carência", "período de carência", "carência de juros", "carência de amortização"],
    ),
    MetricDefinition(
        key="risk_exposure",
        keywords=["pulverizado", "concentrado", "exposição ao risco", "granular"],
    ),
    MetricDefinition(
        key="subordination",
        keywords=["subordinação", "sênior", "mezanino", "cota subordinada"],
    ),
    MetricDefinition(
        key="fii_position_return",
        keywords=["retorno da posição em fii", "rentabilidade de fiis", "gráfico de retorno"],
    ),
]

ALGORITHM_VERSION = "1.0.0-mortgage"


class MortgageTransparencyAnalyzer(TransparencyAnalyzer):
    def analyze(self, text: str) -> AnalysisResult:
        normalized_text = text.lower()
        detected_metrics: dict[str, bool] = {}
        weights: dict[str, float] = {}

        for metric in MORTGAGE_METRICS:
            found = any(kw in normalized_text for kw in metric.keywords)
            detected_metrics[metric.key] = found
            weights[metric.key] = 1.0 if found else 0.0

        total_score = sum(weights.values())
        quality_score = total_score / len(MORTGAGE_METRICS)

        return AnalysisResult(
            detected_metrics=detected_metrics,
            weights=weights,
            quality_score=quality_score,
        )

    def get_version(self) -> str:
        return ALGORITHM_VERSION
