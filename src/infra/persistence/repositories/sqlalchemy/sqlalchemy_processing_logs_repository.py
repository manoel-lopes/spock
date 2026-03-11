from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.application.repositories.processing_logs_repository import ProcessingLogsRepository
from src.domain.enterprise.entities.processing_log import ProcessingLog
from src.infra.persistence.mappers.sqlalchemy_mappers import ProcessingLogMapper
from src.infra.persistence.models import ProcessingLogModel


class SqlAlchemyProcessingLogsRepository(ProcessingLogsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        processing_job_id: str,
        stage: str,
        status: str,
        duration_ms: int | None,
        metadata: dict[str, Any] | None,
    ) -> ProcessingLog:
        model = ProcessingLogModel(
            processing_job_id=processing_job_id,
            stage=stage,
            status=status,
            duration_ms=duration_ms,
            metadata_=metadata,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return ProcessingLogMapper.to_domain(model)

    async def find_by_job_id(self, processing_job_id: str) -> list[ProcessingLog]:
        stmt = (
            select(ProcessingLogModel)
            .where(ProcessingLogModel.processing_job_id == processing_job_id)
            .order_by(ProcessingLogModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [ProcessingLogMapper.to_domain(m) for m in result.scalars().all()]
