import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.application.repositories.funds_repository import FundsRepository
from src.shared.domain.application.repositories.reports_repository import ReportsRepository
from src.shared.domain.application.usecases.submit_analysis.submit_analysis_usecase import (
    SubmitAnalysisRequest,
    SubmitAnalysisUseCase,
)
from src.shared.infra.adapters.collectors.ports.report_collector import ReportCollector
from src.shared.infra.env.env import EnvSettings

logger = logging.getLogger(__name__)


@dataclass
class DiscoverFundReportsRequest:
    ticker: str
    reference_date: datetime | None = None


@dataclass
class DiscoverFundReportsResponse:
    discovered: int
    submitted: int
    skipped: int


class DiscoverFundReportsUseCase:
    def __init__(
        self,
        funds_repository: FundsRepository,
        reports_repository: ReportsRepository,
        report_collector: ReportCollector,
        submit_analysis_usecase: SubmitAnalysisUseCase,
        env_service: EnvSettings,
        session: AsyncSession,
    ) -> None:
        self._funds_repository = funds_repository
        self._reports_repository = reports_repository
        self._report_collector = report_collector
        self._submit_analysis_usecase = submit_analysis_usecase
        self._env_service = env_service
        self._session = session

    async def execute(self, req: DiscoverFundReportsRequest) -> DiscoverFundReportsResponse:
        ticker = req.ticker.lower()

        fund = await self._funds_repository.find_by_ticker(ticker)
        if not fund:
            fund = await self._funds_repository.create(
                ticker=ticker,
                name=ticker,
                manager=None,
                category=None,
                source="discover",
                active=True,
            )
            logger.info("Auto-created fund %s", ticker)

        communications = await self._report_collector.list_communications(ticker)
        reference_date = req.reference_date or datetime.now()
        rolling_window_months = self._env_service.analysis_rolling_window_months

        year_offset = rolling_window_months // 12
        month_offset = rolling_window_months % 12
        new_month = reference_date.month - month_offset
        new_year = reference_date.year - year_offset
        if new_month <= 0:
            new_month += 12
            new_year -= 1
        window_start = datetime(new_year, new_month, min(reference_date.day, 28))

        discovered = 0
        submitted = 0
        skipped = 0

        reports = [c for c in communications if "relatório gerencial" in c.type.lower()]
        logger.info(
            "Found %d 'Relatório Gerencial' out of %d total communications for %s",
            len(reports), len(communications), ticker,
        )

        for item in reports:
            parsed_date = self._parse_date(item.date)
            if not parsed_date or parsed_date < window_start or parsed_date > reference_date:
                continue

            discovered += 1

            if submitted >= rolling_window_months:
                skipped += 1
                continue

            try:
                reference_month = self._previous_month(parsed_date)
                existing = await self._reports_repository.find_by_fund_id_and_month(
                    fund.id, reference_month
                )
                if existing:
                    skipped += 1
                    continue

                pdf_url = await self._report_collector.resolve_pdf_url(item.link_url)
                await self._submit_analysis_usecase.execute(
                    SubmitAnalysisRequest(
                        ticker=ticker,
                        pdf_url=pdf_url,
                        reference_month=reference_month,
                        publication_date=parsed_date,
                    )
                )
                submitted += 1
            except Exception as e:
                await self._session.rollback()
                logger.warning(
                    "Failed to process communication for %s: %s", ticker, str(e)
                )
                skipped += 1

        return DiscoverFundReportsResponse(
            discovered=discovered,
            submitted=submitted,
            skipped=skipped,
        )

    @staticmethod
    def _previous_month(dt: datetime) -> datetime:
        """FII reports published in month N cover month N-1."""
        if dt.month == 1:
            return datetime(dt.year - 1, 12, 1)
        return datetime(dt.year, dt.month - 1, 1)

    def _parse_date(self, date_str: str) -> datetime | None:
        parts = date_str.split("/")
        if len(parts) != 3:
            return None
        try:
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2])
            return datetime(year, month, day)
        except (ValueError, IndexError):
            return None
