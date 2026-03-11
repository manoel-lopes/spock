from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from src.core.domain.application.paginated_items import PaginatedItems
from src.core.domain.application.pagination_params import PaginationParams
from src.domain.enterprise.entities.transparency_score import TransparencyScore


class TransparencyScoresRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        fund_id: str,
        period_start: datetime,
        period_end: datetime,
        regularity: float,
        timeliness: float,
        quality: float,
        final_score: float,
        classification: str,
        algorithm_version: str,
        metadata: dict[str, Any] | None,
    ) -> TransparencyScore: ...

    @abstractmethod
    async def find_latest_by_fund_id(self, fund_id: str) -> TransparencyScore | None: ...

    @abstractmethod
    async def find_by_fund_id_and_period(
        self, fund_id: str, period_start: datetime, period_end: datetime
    ) -> TransparencyScore | None: ...

    @abstractmethod
    async def find_history_by_fund_id(
        self, fund_id: str, params: PaginationParams
    ) -> PaginatedItems[TransparencyScore]: ...
