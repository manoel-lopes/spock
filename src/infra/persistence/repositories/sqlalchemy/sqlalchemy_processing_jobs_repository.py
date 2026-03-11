from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.application.repositories.processing_jobs_repository import ProcessingJobsRepository
from src.domain.enterprise.entities.processing_job import ProcessingJob
from src.infra.persistence.mappers.sqlalchemy_mappers import ProcessingJobMapper
from src.infra.persistence.models import ProcessingJobModel


class SqlAlchemyProcessingJobsRepository(ProcessingJobsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        external_job_id: str,
        type: str,
        payload: dict[str, Any],
        status: str,
        attempts: int,
        started_at: datetime | None,
        completed_at: datetime | None,
        error_message: str | None,
    ) -> ProcessingJob:
        model = ProcessingJobModel(
            external_job_id=external_job_id,
            type=type,
            payload=payload,
            status=status,
            attempts=attempts,
            started_at=started_at,
            completed_at=completed_at,
            error_message=error_message,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return ProcessingJobMapper.to_domain(model)

    async def find_by_external_job_id(self, external_job_id: str) -> ProcessingJob | None:
        stmt = select(ProcessingJobModel).where(
            ProcessingJobModel.external_job_id == external_job_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return ProcessingJobMapper.to_domain(model)

    async def update_status(
        self,
        job_id: str,
        status: str,
        *,
        error_message: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        attempts: int | None = None,
    ) -> ProcessingJob:
        model = await self._session.get(ProcessingJobModel, job_id)
        if not model:
            raise ValueError(f"ProcessingJob {job_id} not found")
        model.status = status
        if error_message is not None:
            model.error_message = error_message
        if started_at is not None:
            model.started_at = started_at
        if completed_at is not None:
            model.completed_at = completed_at
        if attempts is not None:
            model.attempts = attempts
        await self._session.commit()
        await self._session.refresh(model)
        return ProcessingJobMapper.to_domain(model)

    async def find_pending_by_payload(
        self, type: str, payload: dict[str, Any]
    ) -> ProcessingJob | None:
        stmt = select(ProcessingJobModel).where(
            ProcessingJobModel.type == type,
            ProcessingJobModel.payload == payload,
            ProcessingJobModel.status.in_(["pending", "processing"]),
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None
        return ProcessingJobMapper.to_domain(model)

    async def update_external_job_id(
        self, job_id: str, external_job_id: str
    ) -> ProcessingJob:
        model = await self._session.get(ProcessingJobModel, job_id)
        if not model:
            raise ValueError(f"ProcessingJob {job_id} not found")
        model.external_job_id = external_job_id
        await self._session.commit()
        await self._session.refresh(model)
        return ProcessingJobMapper.to_domain(model)
