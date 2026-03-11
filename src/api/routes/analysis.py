from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.dependencies import (
    get_get_analysis_result_usecase,
    get_reprocess_analysis_usecase,
    get_submit_analysis_usecase,
)
from src.domain.application.usecases.get_analysis_result.get_analysis_result_usecase import (
    GetAnalysisResultRequest,
    GetAnalysisResultUseCase,
)
from src.domain.application.usecases.reprocess_analysis.reprocess_analysis_usecase import (
    ReprocessAnalysisRequest,
    ReprocessAnalysisUseCase,
)
from src.domain.application.usecases.submit_analysis.errors.duplicate_job import DuplicateJobError
from src.domain.application.usecases.submit_analysis.submit_analysis_usecase import (
    SubmitAnalysisRequest,
    SubmitAnalysisUseCase,
)
from src.infra.auth.guards.api_key_auth import require_api_key
from src.shared.application.errors.resource_not_found import ResourceNotFoundError

router = APIRouter(prefix="/reports", tags=["Reports"], dependencies=[Depends(require_api_key)])


class SubmitAnalysisBody(BaseModel):
    ticker: str
    pdf_url: str
    reference_month: str


class ReprocessBody(BaseModel):
    report_id: str


@router.post("/analyze", status_code=202)
async def submit_analysis(
    body: SubmitAnalysisBody,
    usecase: SubmitAnalysisUseCase = Depends(get_submit_analysis_usecase),
):
    try:
        result = await usecase.execute(
            SubmitAnalysisRequest(
                ticker=body.ticker,
                pdf_url=body.pdf_url,
                reference_month=datetime.fromisoformat(body.reference_month),
            )
        )
        return {"jobId": result.job_id, "reportId": result.report_id}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DuplicateJobError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("/{report_id}")
async def get_analysis_result(
    report_id: str,
    usecase: GetAnalysisResultUseCase = Depends(get_get_analysis_result_usecase),
):
    try:
        result = await usecase.execute(GetAnalysisResultRequest(report_id=report_id))
        return {
            "report": result.report.model_dump(),
            "content": result.content.model_dump() if result.content else None,
            "analysis": result.analysis.model_dump() if result.analysis else None,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/reprocess", status_code=202)
async def reprocess_analysis(
    body: ReprocessBody,
    usecase: ReprocessAnalysisUseCase = Depends(get_reprocess_analysis_usecase),
):
    try:
        result = await usecase.execute(ReprocessAnalysisRequest(report_id=body.report_id))
        return {"jobId": result.job_id}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
