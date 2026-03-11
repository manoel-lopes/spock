from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.dependencies import (
    get_discover_fund_reports_usecase,
    get_get_fund_transparency_history_usecase,
    get_get_fund_transparency_usecase,
)
from src.domain.application.usecases.discover_fund_reports.discover_fund_reports_usecase import (
    DiscoverFundReportsRequest,
    DiscoverFundReportsUseCase,
)
from src.domain.application.usecases.get_fund_transparency.get_fund_transparency_usecase import (
    GetFundTransparencyRequest,
    GetFundTransparencyUseCase,
)
from src.domain.application.usecases.get_fund_transparency_history.get_fund_transparency_history_usecase import (
    GetFundTransparencyHistoryRequest,
    GetFundTransparencyHistoryUseCase,
)
from src.infra.auth.guards.api_key_auth import require_api_key
from src.shared.application.errors.resource_not_found import ResourceNotFoundError

router = APIRouter(prefix="/funds", tags=["Funds"], dependencies=[Depends(require_api_key)])


class DiscoverBody(BaseModel):
    reference_date: datetime | None = None


@router.post("/{ticker}/discover")
async def discover_fund_reports(
    ticker: str,
    body: DiscoverBody | None = None,
    usecase: DiscoverFundReportsUseCase = Depends(get_discover_fund_reports_usecase),
):
    try:
        result = await usecase.execute(
            DiscoverFundReportsRequest(
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


@router.get("/{ticker}/transparency")
async def get_fund_transparency(
    ticker: str,
    usecase: GetFundTransparencyUseCase = Depends(get_get_fund_transparency_usecase),
):
    try:
        result = await usecase.execute(GetFundTransparencyRequest(ticker=ticker))
        return {"score": result.score.model_dump()}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{ticker}/transparency/history")
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
