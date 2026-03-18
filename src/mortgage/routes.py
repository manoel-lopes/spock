from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.mortgage.dependencies import (
    get_discover_and_analyze_usecase,
    get_get_analysis_result_usecase,
    get_get_fund_transparency_history_usecase,
    get_get_fund_transparency_usecase,
)
from src.shared.domain.application.usecases.discover_and_analyze.discover_and_analyze_usecase import (
    DiscoverAndAnalyzeRequest,
    DiscoverAndAnalyzeUseCase,
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
from src.shared.errors.resource_not_found import ResourceNotFoundError
from src.shared.infra.auth.guards.api_key_auth import require_api_key

router = APIRouter(prefix="/mortgage", tags=["Mortgage"], dependencies=[Depends(require_api_key)])


class DiscoverBody(BaseModel):
    reference_date: datetime | None = None


# --- Fund routes ---


@router.post("/funds/{ticker}/discover")
async def discover_fund_reports(
    ticker: str,
    body: DiscoverBody | None = None,
    max_reports: int = Query(default=4, ge=1, le=24, alias="maxReports"),
    usecase: DiscoverAndAnalyzeUseCase = Depends(get_discover_and_analyze_usecase),
):
    try:
        result = await usecase.execute(
            DiscoverAndAnalyzeRequest(
                ticker=ticker,
                fund_type="mortgage",
                max_reports=max_reports,
                reference_date=body.reference_date if body else None,
            )
        )
        return {
            "discovered": result.discovered,
            "analyzed": result.analyzed,
            "cached": result.cached,
            "failed": result.failed,
            "remaining": result.remaining,
            "score": result.score,
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
    try:
        result = await usecase.execute(GetFundTransparencyRequest(ticker=ticker))
        return {"score": result.score.model_dump()}
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
    try:
        result = await usecase.execute(
            GetFundTransparencyHistoryRequest(
                ticker=ticker,
                page=page,
                page_size=page_size,
                order=order,
            )
        )
        return {
            "page": result.page,
            "pageSize": result.page_size,
            "totalItems": result.total_items,
            "totalPages": result.total_pages,
            "items": [item.model_dump() for item in result.items],
            "order": result.order,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


# --- Report routes ---


@router.get("/reports/{report_id}")
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
