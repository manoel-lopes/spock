from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.application.repositories.report_analyses_repository import ReportAnalysesRepository
from src.shared.domain.enterprise.entities.report_analysis import ReportAnalysis
from src.shared.infra.persistence.mappers.sqlalchemy_mappers import ReportAnalysisMapper
from src.shared.infra.persistence.models import ReportAnalysisModel


class SqlAlchemyReportAnalysesRepository(ReportAnalysesRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        report_id: str,
        algorithm_version: str,
        detected_metrics: dict[str, Any],
        weights: dict[str, Any],
        quality_score: float,
    ) -> ReportAnalysis:
        model = ReportAnalysisModel(
            report_id=report_id,
            algorithm_version=algorithm_version,
            detected_metrics=detected_metrics,
            weights=weights,
            quality_score=quality_score,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return ReportAnalysisMapper.to_domain(model)

    async def find_by_report_ids(self, report_ids: list[str]) -> list[ReportAnalysis]:
        if not report_ids:
            return []
        stmt = select(ReportAnalysisModel).where(ReportAnalysisModel.report_id.in_(report_ids))
        result = await self._session.execute(stmt)
        return [ReportAnalysisMapper.to_domain(m) for m in result.scalars().all()]

    async def find_by_report_id_and_version(
        self, report_id: str, algorithm_version: str
    ) -> ReportAnalysis | None:
        stmt = select(ReportAnalysisModel).where(
            and_(
                ReportAnalysisModel.report_id == report_id,
                ReportAnalysisModel.algorithm_version == algorithm_version,
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return ReportAnalysisMapper.to_domain(model)
