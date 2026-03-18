import logging
import time
from dataclasses import dataclass
from datetime import datetime
from dateutil.relativedelta import relativedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.core.domain.application.pagination_params import PaginationParams
from src.shared.domain.application.repositories.funds_repository import FundsRepository
from src.shared.domain.application.repositories.report_analyses_repository import ReportAnalysesRepository
from src.shared.domain.application.repositories.report_contents_repository import ReportContentsRepository
from src.shared.domain.application.repositories.reports_repository import ReportsRepository
from src.shared.domain.application.repositories.transparency_scores_repository import TransparencyScoresRepository
from src.shared.domain.application.services.report_processor import PermanentFailure, ReportProcessor
from src.shared.infra.adapters.collectors.ports.report_collector import ReportCollector
from src.shared.infra.adapters.scoring.ports.transparency_score_calculator import (
    TransparencyScoreCalculator,
    TransparencyScoreInput,
)
from src.shared.infra.env.env import EnvSettings

logger = logging.getLogger(__name__)

TIMEOUT_SAFETY_SECONDS = 25


@dataclass
class DiscoverAndAnalyzeRequest:
    ticker: str
    fund_type: str
    max_reports: int = 3
    reference_date: datetime | None = None


@dataclass
class DiscoverAndAnalyzeResponse:
    discovered: int
    analyzed: int
    cached: int
    failed: int
    remaining: int
    score: float | None = None


class DiscoverAndAnalyzeUseCase:
    def __init__(
        self,
        funds_repository: FundsRepository,
        reports_repository: ReportsRepository,
        report_contents_repository: ReportContentsRepository,
        report_analyses_repository: ReportAnalysesRepository,
        transparency_scores_repository: TransparencyScoresRepository,
        report_collector: ReportCollector,
        report_processor: ReportProcessor,
        score_calculator: TransparencyScoreCalculator,
        env_service: EnvSettings,
        session: AsyncSession,
    ) -> None:
        self._funds_repo = funds_repository
        self._reports_repo = reports_repository
        self._contents_repo = report_contents_repository
        self._analyses_repo = report_analyses_repository
        self._scores_repo = transparency_scores_repository
        self._collector = report_collector
        self._processor = report_processor
        self._calculator = score_calculator
        self._env = env_service
        self._session = session

    async def execute(self, req: DiscoverAndAnalyzeRequest) -> DiscoverAndAnalyzeResponse:
        start_time = time.monotonic()
        ticker = req.ticker.lower()

        fund = await self._funds_repo.find_by_ticker(ticker)
        if not fund:
            fund = await self._funds_repo.create(
                ticker=ticker,
                name=ticker,
                fund_type=req.fund_type,
                manager=None,
                category=None,
                source="discover",
                active=True,
            )
            logger.info("Auto-created %s fund %s", req.fund_type, ticker)

        communications = await self._collector.list_communications(ticker)
        reference_date = req.reference_date or datetime.now()
        rolling_window = self._env.analysis_rolling_window_months

        window_start = self._rolling_window_start(reference_date, rolling_window)

        reports_comm = [c for c in communications if "relatório gerencial" in c.type.lower()]
        logger.info(
            "Found %d 'Relatório Gerencial' out of %d total for %s",
            len(reports_comm), len(communications), ticker,
        )

        # Gather candidate reports within the rolling window
        candidates = []
        for item in reports_comm:
            parsed_date = self._parse_date(item.date)
            if not parsed_date or parsed_date < window_start or parsed_date > reference_date:
                continue
            candidates.append((item, parsed_date))

        discovered = len(candidates)
        analyzed = 0
        cached = 0
        failed = 0
        processed_this_call = 0

        for item, parsed_date in candidates:
            reference_month = self._previous_month(parsed_date)

            existing_report = await self._reports_repo.find_by_fund_id_and_month(
                fund.id, reference_month
            )

            if existing_report and existing_report.status == "completed":
                cached += 1
                continue

            # Reset stuck reports (from crashed/timed-out previous calls) for clean retry
            if existing_report and existing_report.status in ("downloading", "extracting", "analyzing", "failed"):
                await self._reports_repo.update_status(existing_report.id, "pending")

            if processed_this_call >= req.max_reports:
                break

            elapsed = time.monotonic() - start_time
            if elapsed > TIMEOUT_SAFETY_SECONDS:
                logger.warning("Approaching timeout (%.1fs), stopping early", elapsed)
                break

            try:
                if not existing_report:
                    pdf_url = await self._collector.resolve_pdf_url(item.link_url)
                    existing_report = await self._reports_repo.create(
                        fund_id=fund.id,
                        reference_month=reference_month,
                        publication_date=parsed_date,
                        pdf_url=pdf_url,
                        pdf_hash=None,
                        status="pending",
                        error_message=None,
                    )

                result = await self._processor.process_report(
                    existing_report, req.fund_type
                )

                if result.cached:
                    cached += 1
                else:
                    analyzed += 1
                processed_this_call += 1

            except PermanentFailure as e:
                logger.warning("Permanent failure for %s/%s: %s", ticker, reference_month, e)
                if existing_report:
                    await self._reports_repo.update_status(
                        existing_report.id, "failed", str(e)
                    )
                failed += 1
                processed_this_call += 1
            except Exception as e:
                await self._session.rollback()
                logger.warning("Failed to process report for %s: %s", ticker, e)
                if existing_report:
                    try:
                        await self._reports_repo.update_status(
                            existing_report.id, "failed", str(e)
                        )
                    except Exception:
                        pass
                failed += 1
                processed_this_call += 1

        remaining = discovered - cached - analyzed - failed
        if remaining < 0:
            remaining = 0

        score = None
        if remaining == 0 and (analyzed > 0 or cached > 0):
            score = await self._calculate_score(fund.id, reference_date, rolling_window)

        return DiscoverAndAnalyzeResponse(
            discovered=discovered,
            analyzed=analyzed,
            cached=cached,
            failed=failed,
            remaining=remaining,
            score=score,
        )

    async def _calculate_score(
        self, fund_id: str, reference_date: datetime, rolling_window: int,
    ) -> float | None:
        try:
            period_end = reference_date
            period_start = self._rolling_window_start(period_end, rolling_window)

            reports = await self._reports_repo.find_by_fund_id_in_period(
                fund_id, period_start, period_end
            )
            completed = [r for r in reports if r.status == "completed"]
            if not completed:
                return None

            report_ids = [r.id for r in completed]
            analyses = await self._analyses_repo.find_by_report_ids(report_ids)

            result = self._calculator.calculate(
                TransparencyScoreInput(
                    reports=completed,
                    analyses=analyses,
                    period_start=period_start,
                    period_end=period_end,
                )
            )

            classification = result.classification
            if classification == "C":
                classification = await self._apply_degradation(fund_id, classification)

            await self._scores_repo.create(
                fund_id=fund_id,
                period_start=period_start,
                period_end=period_end,
                regularity=result.regularity,
                timeliness=result.timeliness,
                quality=result.quality,
                final_score=result.final_score,
                classification=classification,
                algorithm_version=self._env.analysis_algorithm_version,
                metadata={
                    "reportCount": result.metadata.report_count,
                    "expectedReports": result.metadata.expected_reports,
                    "avgDelayDays": result.metadata.avg_delay_days,
                    "avgQualityScore": result.metadata.avg_quality_score,
                },
            )

            return result.final_score
        except Exception as e:
            logger.warning("Scoring failed for fund %s: %s", fund_id, e)
            return None

    async def _apply_degradation(self, fund_id: str, classification: str) -> str:
        history = await self._scores_repo.find_history_by_fund_id(
            fund_id, PaginationParams(page=1, page_size=100, order="desc")
        )
        if not history.items:
            return classification

        first_c_date = None
        for score in history.items:
            if score.classification in ("A", "B"):
                break
            if score.classification in ("C", "D"):
                first_c_date = score.created_at

        if first_c_date and datetime.now() >= first_c_date + relativedelta(months=9):
            return "D"
        return classification

    @staticmethod
    def _rolling_window_start(reference_date: datetime, months: int) -> datetime:
        year_offset = months // 12
        month_offset = months % 12
        new_month = reference_date.month - month_offset
        new_year = reference_date.year - year_offset
        if new_month <= 0:
            new_month += 12
            new_year -= 1
        return datetime(new_year, new_month, min(reference_date.day, 28))

    @staticmethod
    def _previous_month(dt: datetime) -> datetime:
        if dt.month == 1:
            return datetime(dt.year - 1, 12, 1)
        return datetime(dt.year, dt.month - 1, 1)

    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        parts = date_str.split("/")
        if len(parts) != 3:
            return None
        try:
            return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
        except (ValueError, IndexError):
            return None
