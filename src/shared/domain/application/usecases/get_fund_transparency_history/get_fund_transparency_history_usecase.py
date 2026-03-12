from dataclasses import dataclass
from typing import Literal

from src.shared.core.domain.application.paginated_items import PaginatedItems
from src.shared.core.domain.application.pagination_params import PaginationParams
from src.shared.domain.application.repositories.funds_repository import FundsRepository
from src.shared.domain.application.repositories.transparency_scores_repository import TransparencyScoresRepository
from src.shared.domain.enterprise.entities.transparency_score import TransparencyScore
from src.shared.errors.resource_not_found import ResourceNotFoundError


@dataclass
class GetFundTransparencyHistoryRequest:
    ticker: str
    page: int = 1
    page_size: int = 20
    order: Literal["asc", "desc"] = "desc"


class GetFundTransparencyHistoryUseCase:
    def __init__(
        self,
        funds_repository: FundsRepository,
        transparency_scores_repository: TransparencyScoresRepository,
    ) -> None:
        self._funds_repository = funds_repository
        self._transparency_scores_repository = transparency_scores_repository

    async def execute(
        self, req: GetFundTransparencyHistoryRequest
    ) -> PaginatedItems[TransparencyScore]:
        fund = await self._funds_repository.find_by_ticker(req.ticker)
        if not fund:
            raise ResourceNotFoundError("Fund")

        return await self._transparency_scores_repository.find_history_by_fund_id(
            fund.id,
            PaginationParams(
                page=req.page,
                page_size=req.page_size,
                order=req.order,
            ),
        )
