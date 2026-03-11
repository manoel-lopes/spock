from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.application.repositories.report_contents_repository import ReportContentsRepository
from src.domain.enterprise.entities.report_content import ReportContent
from src.infra.persistence.mappers.sqlalchemy_mappers import ReportContentMapper
from src.infra.persistence.models import ReportContentModel


class SqlAlchemyReportContentsRepository(ReportContentsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        report_id: str,
        raw_text: str,
        normalized_text: str | None,
        page_count: int,
        parser_version: str | None,
    ) -> ReportContent:
        model = ReportContentModel(
            report_id=report_id,
            raw_text=raw_text,
            normalized_text=normalized_text,
            page_count=page_count,
            parser_version=parser_version,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return ReportContentMapper.to_domain(model)

    async def find_by_report_id(self, report_id: str) -> ReportContent | None:
        stmt = select(ReportContentModel).where(ReportContentModel.report_id == report_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return ReportContentMapper.to_domain(model)
