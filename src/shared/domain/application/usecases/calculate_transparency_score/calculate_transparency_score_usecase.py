import logging
from dataclasses import dataclass
from datetime import datetime

from src.shared.domain.application.repositories.funds_repository import FundsRepository
from src.shared.domain.application.repositories.report_analyses_repository import ReportAnalysesRepository
from src.shared.domain.application.repositories.reports_repository import ReportsRepository
from src.shared.domain.application.repositories.transparency_scores_repository import TransparencyScoresRepository
from src.shared.domain.enterprise.entities.transparency_score import TransparencyScore
from src.shared.infra.adapters.scoring.ports.transparency_score_calculator import (
    TransparencyScoreCalculator,
    TransparencyScoreInput,
)
from src.shared.infra.env.env import EnvSettings
from src.shared.errors.resource_not_found import ResourceNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class CalculateTransparencyScoreRequest:
    ticker: str
    reference_date: datetime | None = None


@dataclass
class CalculateTransparencyScoreResponse:
    score: TransparencyScore


class CalculateTransparencyScoreUseCase:
    def __init__(
        self,
        funds_repository: FundsRepository,
        reports_repository: ReportsRepository,
        report_analyses_repository: ReportAnalysesRepository,
        transparency_scores_repository: TransparencyScoresRepository,
        score_calculator: TransparencyScoreCalculator,
        env_service: EnvSettings,
    ) -> None:
        self._funds_repository = funds_repository
        self._reports_repository = reports_repository
        self._report_analyses_repository = report_analyses_repository
        self._transparency_scores_repository = transparency_scores_repository
        self._score_calculator = score_calculator
        self._env_service = env_service

    async def execute(
        self, req: CalculateTransparencyScoreRequest
    ) -> CalculateTransparencyScoreResponse:
        fund = await self._funds_repository.find_by_ticker(req.ticker)
        if not fund:
            raise ResourceNotFoundError("Fund")

        period_end = req.reference_date or datetime.now()
        rolling_window_months = self._env_service.analysis_rolling_window_months

        year_offset = rolling_window_months // 12
        month_offset = rolling_window_months % 12
        new_month = period_end.month - month_offset
        new_year = period_end.year - year_offset
        if new_month <= 0:
            new_month += 12
            new_year -= 1
        period_start = datetime(new_year, new_month, min(period_end.day, 28))

        existing = await self._transparency_scores_repository.find_by_fund_id_and_period(
            fund.id, period_start, period_end
        )
        if existing:
            return CalculateTransparencyScoreResponse(score=existing)

        reports = await self._reports_repository.find_by_fund_id_in_period(
            fund.id, period_start, period_end
        )
        report_ids = [r.id for r in reports]
        analyses = (
            await self._report_analyses_repository.find_by_report_ids(report_ids)
            if report_ids
            else []
        )

        result = self._score_calculator.calculate(
            TransparencyScoreInput(
                reports=reports,
                analyses=analyses,
                period_start=period_start,
                period_end=period_end,
            )
        )

        algorithm_version = self._env_service.analysis_algorithm_version

        score = await self._transparency_scores_repository.create(
            fund_id=fund.id,
            period_start=period_start,
            period_end=period_end,
            regularity=result.regularity,
            timeliness=result.timeliness,
            quality=result.quality,
            final_score=result.final_score,
            classification=result.classification,
            algorithm_version=algorithm_version,
            metadata={
                "reportCount": result.metadata.report_count,
                "expectedReports": result.metadata.expected_reports,
                "avgDelayDays": result.metadata.avg_delay_days,
                "avgQualityScore": result.metadata.avg_quality_score,
            },
        )

        return CalculateTransparencyScoreResponse(score=score)
