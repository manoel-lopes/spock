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


class MortgageLlmAnalyzer(LlmTransparencyAnalyzer):
    def __init__(self, api_key: str, model: str) -> None:
        from src.shared.infra.adapters.analysis.implementations.llm_transparency_analyzer import (
            MetricDefinition as LlmMetricDefinition,
        )

        llm_metrics = [
            LlmMetricDefinition(
                key="cri_ratings",
                keywords=["rating", "classificação de risco", "operações de cri"],
                description="Credit ratings assigned by rating agencies (Fitch, S&P, Moody's, Liberum, Austin) to the CRI positions held in the portfolio. Indicates the credit quality distribution of the fund's receivables.",
                scoring_rubric="0.3: Mentions that CRIs have ratings without specifics. 0.7: Lists rating distribution (e.g., '60% AAA, 25% AA') or names agencies. 1.0: Full rating table per CRI with agency, rating, outlook, and any rating changes during the period.",
            ),
            LlmMetricDefinition(
                key="portfolio_movements",
                keywords=["movimentação da carteira", "aquisição de cri", "venda de cri"],
                description="CRI portfolio movements during the period: new acquisitions, sales, maturities, and prepayments. Shows how actively the portfolio is being managed.",
                scoring_rubric="0.3: Mentions that CRIs were bought or sold. 0.7: Lists specific CRIs acquired/sold with volumes or rates. 1.0: Detailed movement table with CRI names, volumes, rates (CDI+/IPCA+), counterparties, and impact on portfolio composition.",
            ),
            LlmMetricDefinition(
                key="stratified_dre",
                keywords=["dre", "demonstração de resultado", "receitas", "despesas", "não recorrente"],
                description="Stratified income statement (DRE): revenue and expense breakdown distinguishing recurring income (CRI interest, FII dividends) from non-recurring items (capital gains, MTM adjustments).",
                scoring_rubric="0.3: Shows a single-line net income figure. 0.7: Breaks down revenue by source (CRI income, FII dividends, gains) and lists major expenses. 1.0: Full DRE with line-by-line categorization, recurring vs non-recurring separation, and comparison to prior period.",
            ),
            LlmMetricDefinition(
                key="accumulated_periods",
                keywords=["acumulado", "12 meses", "year to date", "últimos 12"],
                description="Accumulated performance data over longer horizons: YTD and trailing-12-month figures for income, distributions, and returns. Helps investors see beyond monthly volatility.",
                scoring_rubric="0.3: Mentions a YTD or 12-month figure in passing. 0.7: Shows accumulated dividends and return for the year or trailing 12 months. 1.0: Multi-period comparison table (monthly, YTD, 12M, since inception) with dividend yield, total return, and benchmark comparison.",
            ),
            LlmMetricDefinition(
                key="cost_of_leverage",
                keywords=["custo de alavancagem", "custo da dívida", "cdi +", "ipca +"],
                description="Cost of leverage/borrowings: the interest rate spread the fund pays on its repo operations, CRI liabilities, or other borrowings, typically expressed as CDI+ or IPCA+ basis points.",
                scoring_rubric="0.3: Mentions the fund uses leverage. 0.7: States the average cost of leverage (e.g., 'CDI + 1.8%') or total leverage amount. 1.0: Breaks down leverage by instrument, maturity, rate, counterparty, and shows net carry (asset yield minus funding cost).",
            ),
            LlmMetricDefinition(
                key="fii_book",
                keywords=["book de fiis", "posição em fiis", "cotas de fii", "preço médio"],
                description="FII positions book: the fund's holdings in shares of other FIIs, with entry prices (preço médio), current market prices, and unrealized gains/losses.",
                scoring_rubric="0.3: Mentions the fund holds other FII shares. 0.7: Lists FII positions with names and allocation percentages. 1.0: Full position table with ticker, quantity, average cost, current price, unrealized P&L, and dividend yield per position.",
            ),
            LlmMetricDefinition(
                key="sector_diversification",
                keywords=["diversificação setorial", "securitizadora", "concentração por setor"],
                description="Sector diversification of the CRI portfolio: breakdown by underlying real estate sector (residential, commercial, logistics, loteamento) and by originator/securitizer.",
                scoring_rubric="0.3: Mentions the portfolio is diversified. 0.7: Shows sector allocation percentages or top originators. 1.0: Detailed pie/bar chart data with sector %, originator concentration, geographic distribution, and comparison to prior period.",
            ),
            LlmMetricDefinition(
                key="accumulated_reserves",
                keywords=["reserva acumulada", "resultado acumulado", "reserva de contingência"],
                description="Accumulated undistributed income reserves: retained earnings set aside for future distributions, smoothing dividends, or absorbing potential losses.",
                scoring_rubric="0.3: Mentions reserves exist. 0.7: States the current reserve balance in R$ or R$/share. 1.0: Shows reserve evolution over time, reserve policy, and how many months of distributions the reserve covers.",
            ),
            LlmMetricDefinition(
                key="pdd_cris",
                keywords=["pdd", "provisão para devedores duvidosos", "inadimplência de cri"],
                description="Provision for doubtful debtors (PDD) on CRI positions: allowances set aside for CRIs with credit deterioration or expected losses.",
                scoring_rubric="0.3: Mentions PDD exists or is zero. 0.7: States PDD amount and which CRIs are provisioned. 1.0: Detailed PDD table per CRI with provision %, stage classification, recovery expectations, and movement during the period.",
            ),
            LlmMetricDefinition(
                key="dividend_guidance",
                keywords=["distribuição de rendimento", "dividendo", "guidance", "projeção de dividendo"],
                description="Forward-looking dividend guidance: management's projection or indication of expected future distributions per share, including any caveats or conditions.",
                scoring_rubric="0.3: States the current month's dividend without forward context. 0.7: Provides an expected range or target for next month's/quarter's dividend. 1.0: Multi-month projection with assumptions, scenario analysis, or explicit guidance range with supporting calculations.",
            ),
            LlmMetricDefinition(
                key="nonperforming_comments",
                keywords=["inadimplência", "reestruturação", "renegociação", "default", "não performado"],
                description="Commentary on non-performing or restructured CRI positions: discussion of defaulted CRIs, restructuring terms, recovery prospects, and legal actions taken.",
                scoring_rubric="0.3: Mentions defaults exist or all CRIs are performing. 0.7: Names specific non-performing CRIs with status updates. 1.0: Detailed case-by-case discussion with restructuring terms, collateral status, recovery timeline, and legal proceedings.",
            ),
            LlmMetricDefinition(
                key="grace_period",
                keywords=["carência", "período de carência", "carência de juros", "carência de amortização"],
                description="CRIs in grace period (carência): positions where interest or amortization payments are temporarily deferred, typically in newly originated CRIs.",
                scoring_rubric="0.3: Mentions grace periods exist. 0.7: States which CRIs are in grace period and expected end dates. 1.0: Table of CRIs in grace with type (interest/amortization), start/end dates, and impact on current income.",
            ),
            LlmMetricDefinition(
                key="risk_exposure",
                keywords=["pulverizado", "concentrado", "exposição ao risco", "granular"],
                description="Risk exposure profile: whether CRI positions are backed by concentrated (single-debtor) or pulverized (many small debtors) collateral, indicating default correlation risk.",
                scoring_rubric="0.3: Mentions the portfolio has concentrated or pulverized CRIs. 0.7: Shows percentage split between concentrated vs pulverized exposure. 1.0: Detailed breakdown per CRI with exposure type, number of underlying debtors, largest single-debtor exposure, and LTV ratios.",
            ),
            LlmMetricDefinition(
                key="subordination",
                keywords=["subordinação", "sênior", "mezanino", "cota subordinada"],
                description="CRI tranche structure: the seniority level of CRI positions held (senior, mezzanine, subordinated) and the subordination ratios providing credit enhancement.",
                scoring_rubric="0.3: Mentions the fund holds senior or subordinated CRIs. 0.7: Shows the distribution of positions by seniority level with subordination percentages. 1.0: Per-CRI subordination table with tranche, subordination ratio, credit enhancement %, and stress-test scenarios.",
            ),
            LlmMetricDefinition(
                key="fii_position_return",
                keywords=["retorno da posição em fii", "rentabilidade de fiis", "gráfico de retorno"],
                description="Return attribution for FII positions: performance breakdown of FII holdings showing capital gains, dividend income, and total return per position.",
                scoring_rubric="0.3: Mentions returns from FII positions in aggregate. 0.7: Shows total return from FII book with some breakdown. 1.0: Per-position return table with capital gain, dividends received, total return %, and benchmark comparison.",
            ),
        ]
        super().__init__(
            metrics=llm_metrics,
            api_key=api_key,
            model=model,
            fallback_analyzer=MortgageTransparencyAnalyzer(),
            fund_type_label="Mortgage (Papel/CRI)",
        )
