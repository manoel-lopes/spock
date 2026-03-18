from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.application.repositories.reports_repository import ReportsRepository
from src.shared.domain.enterprise.entities.report import Report
from src.shared.infra.persistence.mappers.sqlalchemy_mappers import ReportMapper
from src.shared.infra.persistence.models import ReportModel


class SqlAlchemyReportsRepository(ReportsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        fund_id: str,
        reference_month: datetime,
        publication_date: datetime | None,
        pdf_url: str,
        pdf_hash: str | None,
        status: str,
        error_message: str | None,
    ) -> Report:
        model = ReportModel(
            fund_id=fund_id,
            reference_month=reference_month,
            publication_date=publication_date,
            pdf_url=pdf_url,
            pdf_hash=pdf_hash,
            status=status,
            error_message=error_message,
        )
        self._session.add(model)
        await self._session.commit()
        return ReportMapper.to_domain(model)

    async def find_by_id(self, report_id: str) -> Report | None:
        result = await self._session.get(ReportModel, report_id)
        if not result:
            return None
        return ReportMapper.to_domain(result)

    async def find_by_fund_id_and_month(self, fund_id: str, reference_month: datetime) -> Report | None:
        stmt = select(ReportModel).where(
            ReportModel.fund_id == fund_id,
            ReportModel.reference_month == reference_month,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return ReportMapper.to_domain(model)

    async def find_by_fund_id(self, fund_id: str) -> list[Report]:
        stmt = (
            select(ReportModel)
            .where(ReportModel.fund_id == fund_id)
            .order_by(ReportModel.reference_month.desc())
        )
        result = await self._session.execute(stmt)
        return [ReportMapper.to_domain(m) for m in result.scalars().all()]

    async def find_by_fund_id_in_period(
        self, fund_id: str, period_start: datetime, period_end: datetime
    ) -> list[Report]:
        stmt = (
            select(ReportModel)
            .where(
                ReportModel.fund_id == fund_id,
                ReportModel.reference_month >= period_start,
                ReportModel.reference_month <= period_end,
            )
            .order_by(ReportModel.reference_month.desc())
        )
        result = await self._session.execute(stmt)
        return [ReportMapper.to_domain(m) for m in result.scalars().all()]

    async def update_status(
        self, report_id: str, status: str, error_message: str | None = None
    ) -> Report:
        model = await self._session.get(ReportModel, report_id)
        if not model:
            raise ValueError(f"Report {report_id} not found")
        model.status = status
        model.error_message = error_message
        await self._session.commit()
        return ReportMapper.to_domain(model)

    async def update_pdf_hash(self, report_id: str, pdf_hash: str) -> Report:
        model = await self._session.get(ReportModel, report_id)
        if not model:
            raise ValueError(f"Report {report_id} not found")
        model.pdf_hash = pdf_hash
        await self._session.commit()
        return ReportMapper.to_domain(model)
