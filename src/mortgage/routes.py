from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.mortgage.dependencies import (
    get_discover_mortgage_reports_usecase,
    get_get_analysis_result_usecase,
    get_get_fund_transparency_history_usecase,
    get_get_fund_transparency_usecase,
    get_get_job_status_usecase,
    get_reprocess_analysis_usecase,
    get_submit_mortgage_analysis_usecase,
)
from src.mortgage.usecases.discover_mortgage_reports import (
    DiscoverMortgageReportsRequest,
    DiscoverMortgageReportsUseCase,
)
from src.mortgage.usecases.submit_mortgage_analysis import (
    SubmitMortgageAnalysisRequest,
    SubmitMortgageAnalysisUseCase,
)
from src.shared.domain.application.usecases.get_analysis_result.get_analysis_result_usecase import (
    GetAnalysisResultRequest,
    GetAnalysisResultUseCase,
)
from src.shared.domain.application.usecases.get_fund_transparency.get_fund_transparency_usecase import (
    GetFundTransparencyRequest,
    GetFundTransparencyUseCase,
)
from src.shared.domain.application.usecases.get_fund_transparency_history.get_fund_transparency_history_usecase import (
    GetFundTransparencyHistoryRequest,
    GetFundTransparencyHistoryUseCase,
)
from src.shared.domain.application.usecases.get_job_status.get_job_status_usecase import (
    GetJobStatusRequest,
    GetJobStatusUseCase,
)
from src.shared.domain.application.usecases.reprocess_analysis.reprocess_analysis_usecase import (
    ReprocessAnalysisRequest,
    ReprocessAnalysisUseCase,
)
from src.shared.errors.duplicate_job import DuplicateJobError
from src.shared.errors.resource_not_found import ResourceNotFoundError
from src.shared.infra.auth.guards.api_key_auth import require_api_key
from src.shared.infra.cache.redis_cache import cache_delete, cache_get, cache_set

router = APIRouter(prefix="/mortgage", tags=["Mortgage"], dependencies=[Depends(require_api_key)])

# Cache TTLs (seconds)
TRANSPARENCY_TTL = 600      # 10 min
HISTORY_TTL = 600            # 10 min
ANALYSIS_RESULT_TTL = 3600   # 1 hour
JOB_STATUS_TTL = 15          # 15 sec


class DiscoverBody(BaseModel):
    reference_date: datetime | None = None


class SubmitAnalysisBody(BaseModel):
    ticker: str
    pdf_url: str
    reference_month: str


class ReprocessBody(BaseModel):
    report_id: str


# --- Fund routes ---


@router.post("/funds/{ticker}/discover")
async def discover_fund_reports(
    ticker: str,
    body: DiscoverBody | None = None,
    usecase: DiscoverMortgageReportsUseCase = Depends(get_discover_mortgage_reports_usecase),
):
    await cache_delete(f"mortgage:transparency:{ticker.lower()}*")

    try:
        result = await usecase.execute(
            DiscoverMortgageReportsRequest(
                ticker=ticker,
                reference_date=body.reference_date if body else None,
            )
        )
        return {
            "discovered": result.discovered,
            "submitted": result.submitted,
            "skipped": result.skipped,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Discovery failed: {e}") from e


@router.get("/funds/{ticker}/transparency")
async def get_fund_transparency(
    ticker: str,
    usecase: GetFundTransparencyUseCase = Depends(get_get_fund_transparency_usecase),
):
    cache_key = f"mortgage:transparency:{ticker.lower()}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        result = await usecase.execute(GetFundTransparencyRequest(ticker=ticker))
        response = {"score": result.score.model_dump()}
        await cache_set(cache_key, response, TRANSPARENCY_TTL)
        return response
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/funds/{ticker}/transparency/history")
async def get_fund_transparency_history(
    ticker: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    order: Literal["asc", "desc"] = Query(default="desc"),
    usecase: GetFundTransparencyHistoryUseCase = Depends(get_get_fund_transparency_history_usecase),
):
    cache_key = f"mortgage:transparency:history:{ticker.lower()}:p{page}:ps{page_size}:{order}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        result = await usecase.execute(
            GetFundTransparencyHistoryRequest(
                ticker=ticker,
                page=page,
                page_size=page_size,
                order=order,
            )
        )
        response = {
            "page": result.page,
            "pageSize": result.page_size,
            "totalItems": result.total_items,
            "totalPages": result.total_pages,
            "items": [item.model_dump() for item in result.items],
            "order": result.order,
        }
        await cache_set(cache_key, response, HISTORY_TTL)
        return response
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


# --- Report routes ---


@router.post("/reports/analyze", status_code=202)
async def submit_analysis(
    body: SubmitAnalysisBody,
    usecase: SubmitMortgageAnalysisUseCase = Depends(get_submit_mortgage_analysis_usecase),
):
    try:
        result = await usecase.execute(
            SubmitMortgageAnalysisRequest(
                ticker=body.ticker,
                pdf_url=body.pdf_url,
                reference_month=datetime.fromisoformat(body.reference_month),
            )
        )
        await cache_delete(f"mortgage:transparency:{body.ticker.lower()}*")

        return {"jobId": result.job_id, "reportId": result.report_id}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DuplicateJobError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("/reports/{report_id}")
async def get_analysis_result(
    report_id: str,
    usecase: GetAnalysisResultUseCase = Depends(get_get_analysis_result_usecase),
):
    cache_key = f"mortgage:report:{report_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        result = await usecase.execute(GetAnalysisResultRequest(report_id=report_id))
        response = {
            "report": result.report.model_dump(),
            "content": result.content.model_dump() if result.content else None,
            "analysis": result.analysis.model_dump() if result.analysis else None,
        }
        if result.report.status == "completed":
            await cache_set(cache_key, response, ANALYSIS_RESULT_TTL)
        return response
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/reports/reprocess", status_code=202)
async def reprocess_analysis(
    body: ReprocessBody,
    usecase: ReprocessAnalysisUseCase = Depends(get_reprocess_analysis_usecase),
):
    try:
        result = await usecase.execute(ReprocessAnalysisRequest(report_id=body.report_id))
        await cache_delete(f"mortgage:report:{body.report_id}")
        return {"jobId": result.job_id}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/reports/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    usecase: GetJobStatusUseCase = Depends(get_get_job_status_usecase),
):
    cache_key = f"mortgage:job:{job_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        job = await usecase.execute(GetJobStatusRequest(job_id=job_id))
        response = {"job": job.model_dump()}
        ttl = ANALYSIS_RESULT_TTL if job.status in ("completed", "failed") else JOB_STATUS_TTL
        await cache_set(cache_key, response, ttl)
        return response
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
