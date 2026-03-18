from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.application.services.report_processor import ReportProcessor
from src.shared.domain.application.usecases.calculate_transparency_score.calculate_transparency_score_usecase import (
    CalculateTransparencyScoreUseCase,
)
from src.shared.domain.application.usecases.discover_and_analyze.discover_and_analyze_usecase import (
    DiscoverAndAnalyzeUseCase,
)
from src.shared.domain.application.usecases.get_analysis_result.get_analysis_result_usecase import (
    GetAnalysisResultUseCase,
)
from src.shared.domain.application.usecases.get_fund_transparency.get_fund_transparency_usecase import (
    GetFundTransparencyUseCase,
)
from src.shared.domain.application.usecases.get_fund_transparency_history.get_fund_transparency_history_usecase import (
    GetFundTransparencyHistoryUseCase,
)
from src.shared.infra.adapters.collectors.implementations.http_report_collector import (
    HttpReportCollector,
)
from src.shared.infra.adapters.scoring.implementations.weighted_transparency_score_calculator import (
    WeightedTransparencyScoreCalculator,
)
from src.shared.infra.env.env_service import env_service
from src.shared.infra.persistence.repositories.sqlalchemy.sqlalchemy_funds_repository import (
    SqlAlchemyFundsRepository,
)
from src.shared.infra.persistence.repositories.sqlalchemy.sqlalchemy_report_analyses_repository import (
    SqlAlchemyReportAnalysesRepository,
)
from src.shared.infra.persistence.repositories.sqlalchemy.sqlalchemy_report_contents_repository import (
    SqlAlchemyReportContentsRepository,
)
from src.shared.infra.persistence.repositories.sqlalchemy.sqlalchemy_reports_repository import (
    SqlAlchemyReportsRepository,
)
from src.shared.infra.persistence.repositories.sqlalchemy.sqlalchemy_transparency_scores_repository import (
    SqlAlchemyTransparencyScoresRepository,
)
from src.shared.infra.persistence.session import get_session


# --- Repositories ---


async def get_funds_repository(
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyFundsRepository:
    return SqlAlchemyFundsRepository(session)


async def get_reports_repository(
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyReportsRepository:
    return SqlAlchemyReportsRepository(session)


async def get_report_contents_repository(
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyReportContentsRepository:
    return SqlAlchemyReportContentsRepository(session)


async def get_report_analyses_repository(
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyReportAnalysesRepository:
    return SqlAlchemyReportAnalysesRepository(session)


async def get_transparency_scores_repository(
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyTransparencyScoresRepository:
    return SqlAlchemyTransparencyScoresRepository(session)


# --- Adapters ---


def get_report_collector() -> HttpReportCollector:
    return HttpReportCollector(env_service)


def get_score_calculator() -> WeightedTransparencyScoreCalculator:
    return WeightedTransparencyScoreCalculator(env_service)


# --- Services ---


async def get_report_processor(
    reports_repo: SqlAlchemyReportsRepository = Depends(get_reports_repository),
    contents_repo: SqlAlchemyReportContentsRepository = Depends(get_report_contents_repository),
    analyses_repo: SqlAlchemyReportAnalysesRepository = Depends(get_report_analyses_repository),
) -> ReportProcessor:
    return ReportProcessor(reports_repo, contents_repo, analyses_repo)


# --- Use Cases ---


async def get_discover_and_analyze_usecase(
    session: AsyncSession = Depends(get_session),
    funds_repo: SqlAlchemyFundsRepository = Depends(get_funds_repository),
    reports_repo: SqlAlchemyReportsRepository = Depends(get_reports_repository),
    contents_repo: SqlAlchemyReportContentsRepository = Depends(get_report_contents_repository),
    analyses_repo: SqlAlchemyReportAnalysesRepository = Depends(get_report_analyses_repository),
    scores_repo: SqlAlchemyTransparencyScoresRepository = Depends(get_transparency_scores_repository),
    report_collector: HttpReportCollector = Depends(get_report_collector),
    report_processor: ReportProcessor = Depends(get_report_processor),
    calculator: WeightedTransparencyScoreCalculator = Depends(get_score_calculator),
) -> DiscoverAndAnalyzeUseCase:
    return DiscoverAndAnalyzeUseCase(
        funds_repo,
        reports_repo,
        contents_repo,
        analyses_repo,
        scores_repo,
        report_collector,
        report_processor,
        calculator,
        env_service,
        session,
    )


async def get_get_analysis_result_usecase(
    reports_repo: SqlAlchemyReportsRepository = Depends(get_reports_repository),
    contents_repo: SqlAlchemyReportContentsRepository = Depends(get_report_contents_repository),
    analyses_repo: SqlAlchemyReportAnalysesRepository = Depends(get_report_analyses_repository),
) -> GetAnalysisResultUseCase:
    return GetAnalysisResultUseCase(reports_repo, contents_repo, analyses_repo)


async def get_get_fund_transparency_usecase(
    funds_repo: SqlAlchemyFundsRepository = Depends(get_funds_repository),
    scores_repo: SqlAlchemyTransparencyScoresRepository = Depends(get_transparency_scores_repository),
) -> GetFundTransparencyUseCase:
    return GetFundTransparencyUseCase(funds_repo, scores_repo)


async def get_get_fund_transparency_history_usecase(
    funds_repo: SqlAlchemyFundsRepository = Depends(get_funds_repository),
    scores_repo: SqlAlchemyTransparencyScoresRepository = Depends(get_transparency_scores_repository),
) -> GetFundTransparencyHistoryUseCase:
    return GetFundTransparencyHistoryUseCase(funds_repo, scores_repo)


async def get_calculate_transparency_score_usecase(
    funds_repo: SqlAlchemyFundsRepository = Depends(get_funds_repository),
    reports_repo: SqlAlchemyReportsRepository = Depends(get_reports_repository),
    analyses_repo: SqlAlchemyReportAnalysesRepository = Depends(get_report_analyses_repository),
    scores_repo: SqlAlchemyTransparencyScoresRepository = Depends(get_transparency_scores_repository),
    calculator: WeightedTransparencyScoreCalculator = Depends(get_score_calculator),
) -> CalculateTransparencyScoreUseCase:
    return CalculateTransparencyScoreUseCase(
        funds_repo,
        reports_repo,
        analyses_repo,
        scores_repo,
        calculator,
        env_service,
    )
