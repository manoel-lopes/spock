from calendar import monthrange

from src.domain.enterprise.entities.report import Report
from src.infra.adapters.scoring.ports.transparency_score_calculator import (
    TransparencyScoreCalculator,
    TransparencyScoreInput,
    TransparencyScoreMetadata,
    TransparencyScoreResult,
)
from src.infra.env.env import EnvSettings

SECONDS_PER_DAY = 86400


class WeightedTransparencyScoreCalculator(TransparencyScoreCalculator):
    def __init__(self, env_service: EnvSettings) -> None:
        self._env = env_service

    def calculate(self, input: TransparencyScoreInput) -> TransparencyScoreResult:
        reports = input.reports
        analyses = input.analyses
        period_start = input.period_start
        period_end = input.period_end

        expected_reports = self._months_diff(period_start, period_end)
        completed_reports = [r for r in reports if r.status == "completed"]

        regularity = min(len(completed_reports) / expected_reports, 1.0) if expected_reports > 0 else 0.0

        timeliness_score, avg_delay = self._calculate_timeliness(completed_reports)

        quality, avg_quality_score = self._calculate_quality(reports, analyses)

        w_reg = self._env.scoring_weight_regularity
        w_time = self._env.scoring_weight_timeliness
        w_qual = self._env.scoring_weight_quality

        final_score = w_reg * regularity + w_time * timeliness_score + w_qual * quality

        return TransparencyScoreResult(
            regularity=regularity,
            timeliness=timeliness_score,
            quality=quality,
            final_score=final_score,
            classification="",
            metadata=TransparencyScoreMetadata(
                report_count=len(completed_reports),
                expected_reports=expected_reports,
                avg_delay_days=avg_delay,
                avg_quality_score=avg_quality_score,
            ),
        )

    def _calculate_timeliness(
        self, completed_reports: list[Report]
    ) -> tuple[float, float]:
        limit_days = self._env.scoring_timeliness_limit_days

        delays: list[float] = []
        for r in completed_reports:
            if r.publication_date is None:
                continue
            ref = r.reference_month
            last_day = monthrange(ref.year, ref.month)[1]
            end_of_ref_month = ref.replace(day=last_day)
            delay_seconds = (r.publication_date - end_of_ref_month).total_seconds()
            delays.append(max(0.0, delay_seconds / SECONDS_PER_DAY))

        if not delays:
            return 0.0, 0.0

        avg_delay = sum(delays) / len(delays)
        score = max(0.0, min(1.0, 1.0 - avg_delay / limit_days))
        return score, avg_delay

    def _calculate_quality(
        self,
        reports: list[Report],
        analyses: list,
    ) -> tuple[float, float]:
        report_ids = {r.id for r in reports}
        matched = [a for a in analyses if a.report_id in report_ids]

        if not matched:
            return 0.0, 0.0

        avg_quality_score = sum(a.quality_score for a in matched) / len(matched)
        return avg_quality_score, avg_quality_score

    def _months_diff(self, start, end) -> int:
        return (end.year - start.year) * 12 + (end.month - start.month)
