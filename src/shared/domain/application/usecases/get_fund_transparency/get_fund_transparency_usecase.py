from dataclasses import dataclass

from src.shared.domain.application.repositories.funds_repository import FundsRepository
from src.shared.domain.application.repositories.transparency_scores_repository import TransparencyScoresRepository
from src.shared.domain.enterprise.entities.transparency_score import TransparencyScore
from src.shared.errors.resource_not_found import ResourceNotFoundError


@dataclass
class GetFundTransparencyRequest:
    ticker: str


@dataclass
class GetFundTransparencyResponse:
    score: TransparencyScore


class GetFundTransparencyUseCase:
    def __init__(
        self,
        funds_repository: FundsRepository,
        transparency_scores_repository: TransparencyScoresRepository,
    ) -> None:
        self._funds_repository = funds_repository
        self._transparency_scores_repository = transparency_scores_repository

    async def execute(self, req: GetFundTransparencyRequest) -> GetFundTransparencyResponse:
        fund = await self._funds_repository.find_by_ticker(req.ticker)
        if not fund:
            raise ResourceNotFoundError("Fund")

        score = await self._transparency_scores_repository.find_latest_by_fund_id(fund.id)
        if not score:
            raise ResourceNotFoundError("Fund")

        return GetFundTransparencyResponse(score=score)
