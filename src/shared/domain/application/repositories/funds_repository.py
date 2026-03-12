from abc import ABC, abstractmethod

from src.shared.domain.enterprise.entities.fund import Fund


class FundsRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        ticker: str,
        name: str,
        fund_type: str = "equity",
        manager: str | None,
        category: str | None,
        source: str | None,
        active: bool,
    ) -> Fund: ...

    @abstractmethod
    async def find_by_id(self, fund_id: str) -> Fund | None: ...

    @abstractmethod
    async def find_by_ticker(self, ticker: str) -> Fund | None: ...
