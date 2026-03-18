from dataclasses import dataclass

from src.shared.infra.adapters.analysis.implementations.llm_transparency_analyzer import (
    LlmTransparencyAnalyzer,
)
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


class EquityLlmAnalyzer(LlmTransparencyAnalyzer):
    def __init__(self, api_key: str, model: str) -> None:
        from src.shared.infra.adapters.analysis.implementations.llm_transparency_analyzer import (
            MetricDefinition as LlmMetricDefinition,
        )

        llm_metrics = [
            LlmMetricDefinition(
                key="vacancia_fisica",
                keywords=["vacância física", "taxa de vacância"],
                description="Physical vacancy rate: the percentage of total leasable area (ABL) that is currently unoccupied. A key indicator of asset quality and demand for the fund's properties.",
                scoring_rubric="0.3: Mentions vacancy exists but no number. 0.7: States a specific vacancy rate (e.g., '5.2% de vacância física') or shows occupied vs total area. 1.0: Provides vacancy breakdown by property/region, historical comparison, or movement (entries/exits) during the period.",
            ),
            LlmMetricDefinition(
                key="vacancia_financeira",
                keywords=["vacância financeira"],
                description="Financial vacancy rate: the revenue shortfall from vacant areas expressed as a percentage of potential rental revenue if fully leased. Differs from physical vacancy when rents vary across units.",
                scoring_rubric="0.3: Mentions financial vacancy without a number. 0.7: States a specific financial vacancy percentage or R$ amount of lost revenue. 1.0: Compares financial vs physical vacancy, breaks down by asset, or shows trend over multiple months.",
            ),
            LlmMetricDefinition(
                key="walt",
                keywords=["walt", "prazo médio dos contratos"],
                description="WALT (Weighted Average Lease Term): the average remaining lease duration weighted by rental revenue. Indicates the fund's revenue predictability and re-leasing risk horizon.",
                scoring_rubric="0.3: Mentions lease terms exist but no weighted average. 0.7: States a specific WALT figure (e.g., '4.3 years') or average contract duration. 1.0: Shows WALT breakdown by tenant/property, lease maturity schedule, or contract expiration distribution chart.",
            ),
            LlmMetricDefinition(
                key="inquilinos",
                keywords=["inquilinos", "locatários", "concentração"],
                description="Tenant profile and concentration analysis: identifies who the tenants are, their creditworthiness, sector distribution, and how concentrated rental income is among top tenants.",
                scoring_rubric="0.3: Mentions number of tenants or names one tenant. 0.7: Lists top tenants with their revenue share or provides sector breakdown. 1.0: Full tenant table with names, revenue %, sector, credit rating, or Herfindahl concentration index.",
            ),
            LlmMetricDefinition(
                key="ativos_imoveis",
                keywords=["carteira", "portfólio", "imóveis", "ativos"],
                description="Real estate asset portfolio: description and valuation of the fund's property holdings including location, type (logistics, office, retail), ABL, and appraised values.",
                scoring_rubric="0.3: Mentions the fund owns properties without specifics. 0.7: Lists properties with basic info (name, city, ABL). 1.0: Detailed property table with location, type, ABL, acquisition cost, current appraisal, cap rate per asset, or occupancy per property.",
            ),
            LlmMetricDefinition(
                key="inadimplencia",
                keywords=["inadimplência", "inadimplencia"],
                description="Tenant delinquency/default rate: the percentage of billed rent that is overdue or uncollected. A direct measure of credit risk within the tenant base.",
                scoring_rubric="0.3: Mentions delinquency exists or says 'zero inadimplência'. 0.7: States a specific delinquency rate or R$ amount overdue. 1.0: Breaks down delinquency by aging bucket, tenant, or shows trend over time with recovery actions taken.",
            ),
            LlmMetricDefinition(
                key="cap_rate",
                keywords=["cap rate", "capitalização"],
                description="Capitalization rate: the ratio of net operating income (NOI) to the property's market value or acquisition cost. Indicates the yield generated by the real estate assets themselves.",
                scoring_rubric="0.3: Mentions cap rate concept without a number. 0.7: States a specific cap rate figure for the portfolio. 1.0: Provides cap rate per property, compares to market benchmarks, or shows cap rate evolution over time.",
            ),
            LlmMetricDefinition(
                key="pipeline",
                keywords=["pipeline", "aquisição", "desinvestimento"],
                description="Investment pipeline: planned or in-progress acquisitions, dispositions, developments, or build-to-suit projects that will change the portfolio composition.",
                scoring_rubric="0.3: Vaguely mentions the fund is looking at opportunities. 0.7: Describes a specific acquisition/disposition target with expected value or timeline. 1.0: Details multiple pipeline items with expected cap rates, funding sources, expected closing dates, and impact on portfolio metrics.",
            ),
            LlmMetricDefinition(
                key="divida_alavancagem",
                keywords=["dívida", "endividamento", "alavancagem", "amortização"],
                description="Debt and leverage profile: the fund's outstanding debt, LTV ratio, amortization schedule, cost of debt (spread over CDI/IPCA), and covenant compliance.",
                scoring_rubric="0.3: Mentions the fund has debt or leverage. 0.7: States total debt, LTV ratio, or cost of debt spread. 1.0: Full debt table with instrument types, maturities, rates, amortization schedule, LTV trend, and covenant status.",
            ),
            LlmMetricDefinition(
                key="comentario_gerencial",
                keywords=["perspectiva", "comentário", "análise gerencial"],
                description="Management commentary: qualitative discussion by the fund manager about market outlook, strategy, operational highlights, risks, and the fund's positioning going forward.",
                scoring_rubric="0.3: Generic boilerplate statement with no specific insights. 0.7: Discusses specific market conditions, fund strategy decisions, or operational events with context. 1.0: In-depth forward-looking analysis with market data, strategic rationale, risk assessment, and clear action plans.",
            ),
        ]
        super().__init__(
            metrics=llm_metrics,
            api_key=api_key,
            model=model,
            fallback_analyzer=EquityTransparencyAnalyzer(),
            fund_type_label="Equity (Tijolo)",
        )
