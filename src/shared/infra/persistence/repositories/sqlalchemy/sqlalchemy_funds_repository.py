from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.application.repositories.funds_repository import FundsRepository
from src.shared.domain.enterprise.entities.fund import Fund
from src.shared.infra.persistence.mappers.sqlalchemy_mappers import FundMapper
from src.shared.infra.persistence.models import FundModel


class SqlAlchemyFundsRepository(FundsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
    ) -> Fund:
        model = FundModel(
            ticker=ticker,
            name=name,
            fund_type=fund_type,
            manager=manager,
            category=category,
            source=source,
            active=active,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return FundMapper.to_domain(model)

    async def find_by_id(self, fund_id: str) -> Fund | None:
        result = await self._session.get(FundModel, fund_id)
        if not result:
            return None
        return FundMapper.to_domain(result)

    async def find_by_ticker(self, ticker: str) -> Fund | None:
        stmt = select(FundModel).where(FundModel.ticker == ticker)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return FundMapper.to_domain(model)
