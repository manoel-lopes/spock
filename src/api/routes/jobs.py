from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_get_job_status_usecase
from src.domain.application.usecases.get_job_status.get_job_status_usecase import (
    GetJobStatusRequest,
    GetJobStatusUseCase,
)
from src.infra.auth.guards.api_key_auth import require_api_key
from src.shared.application.errors.resource_not_found import ResourceNotFoundError

router = APIRouter(prefix="/reports/jobs", tags=["Jobs"], dependencies=[Depends(require_api_key)])


@router.get("/{job_id}")
async def get_job_status(
    job_id: str,
    usecase: GetJobStatusUseCase = Depends(get_get_job_status_usecase),
):
    try:
        job = await usecase.execute(GetJobStatusRequest(job_id=job_id))
        return {"job": job.model_dump()}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
