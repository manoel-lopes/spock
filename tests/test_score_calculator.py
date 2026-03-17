from datetime import datetime

from src.shared.domain.enterprise.entities.report import Report
from src.shared.domain.enterprise.entities.report_analysis import ReportAnalysis
from src.shared.infra.adapters.scoring.implementations.weighted_transparency_score_calculator import (
    WeightedTransparencyScoreCalculator,
)
from src.shared.infra.adapters.scoring.ports.transparency_score_calculator import TransparencyScoreInput
from src.shared.infra.env.env import EnvSettings


def _make_env() -> EnvSettings:
    return EnvSettings(
        scoring_weight_regularity=0.4,
        scoring_weight_timeliness=0.3,
        scoring_weight_quality=0.3,
        scoring_timeliness_limit_days=30,
        _env_file=None,
    )


def test_calculate_with_no_reports():
    calculator = WeightedTransparencyScoreCalculator(_make_env())
    result = calculator.calculate(
        TransparencyScoreInput(
            reports=[],
            analyses=[],
            period_start=datetime(2025, 1, 1),
            period_end=datetime(2026, 1, 1),
        )
    )
    assert result.regularity == 0.0
    assert result.timeliness == 0.0
    assert result.quality == 0.0
    assert result.final_score == 0.0
    assert result.classification == "D"


def test_calculate_with_completed_reports():
    now = datetime.now()
    reports = [
        Report(
            id=f"r{i}",
            fund_id="f1",
            reference_month=datetime(2025, i + 1, 1),
            publication_date=datetime(2025, i + 1, 15),
            pdf_url="http://example.com/pdf",
            status="completed",
            created_at=now,
            updated_at=now,
        )
        for i in range(6)
    ]
    analyses = [
        ReportAnalysis(
            id=f"a{i}",
            report_id=f"r{i}",
            algorithm_version="1.0.0",
            detected_metrics={},
            weights={},
            quality_score=0.8,
            created_at=now,
            updated_at=now,
        )
        for i in range(6)
    ]

    calculator = WeightedTransparencyScoreCalculator(_make_env())
    result = calculator.calculate(
        TransparencyScoreInput(
            reports=reports,
            analyses=analyses,
            period_start=datetime(2025, 1, 1),
            period_end=datetime(2026, 1, 1),
        )
    )

    assert result.regularity == 0.5  # 6/12
    assert result.timeliness > 0  # publications within 30 days
    assert abs(result.quality - 0.8) < 1e-10
    assert result.metadata.report_count == 6
    assert result.metadata.expected_reports == 12


def test_classification_thresholds():
    calculator = WeightedTransparencyScoreCalculator(_make_env())
    now = datetime.now()

    # Full score scenario
    reports = [
        Report(
            id=f"r{i}",
            fund_id="f1",
            reference_month=datetime(2025, i + 1, 1),
            publication_date=datetime(2025, i + 1, 2),  # 1 day after start of month
            pdf_url="http://example.com/pdf",
            status="completed",
            created_at=now,
            updated_at=now,
        )
        for i in range(12)
    ]
    analyses = [
        ReportAnalysis(
            id=f"a{i}",
            report_id=f"r{i}",
            algorithm_version="1.0.0",
            detected_metrics={},
            weights={},
            quality_score=1.0,
            created_at=now,
            updated_at=now,
        )
        for i in range(12)
    ]

    result = calculator.calculate(
        TransparencyScoreInput(
            reports=reports,
            analyses=analyses,
            period_start=datetime(2025, 1, 1),
            period_end=datetime(2026, 1, 1),
        )
    )

    assert result.classification == "A"
