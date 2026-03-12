from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.core.domain.application.paginated_items import PaginatedItems
from src.shared.core.domain.application.pagination_params import PaginationParams
from src.shared.domain.application.repositories.transparency_scores_repository import TransparencyScoresRepository
from src.shared.domain.enterprise.entities.transparency_score import TransparencyScore
from src.shared.infra.persistence.mappers.sqlalchemy_mappers import TransparencyScoreMapper
from src.shared.infra.persistence.models import TransparencyScoreModel


class SqlAlchemyTransparencyScoresRepository(TransparencyScoresRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
    ) -> TransparencyScore:
        model = TransparencyScoreModel(
            fund_id=fund_id,
            period_start=period_start,
            period_end=period_end,
            regularity=regularity,
            timeliness=timeliness,
            quality=quality,
            final_score=final_score,
            classification=classification,
            algorithm_version=algorithm_version,
            metadata_=metadata,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return TransparencyScoreMapper.to_domain(model)

    async def find_latest_by_fund_id(self, fund_id: str) -> TransparencyScore | None:
        stmt = (
            select(TransparencyScoreModel)
            .where(TransparencyScoreModel.fund_id == fund_id)
            .order_by(TransparencyScoreModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return TransparencyScoreMapper.to_domain(model)

    async def find_by_fund_id_and_period(
        self, fund_id: str, period_start: datetime, period_end: datetime
    ) -> TransparencyScore | None:
        stmt = select(TransparencyScoreModel).where(
            TransparencyScoreModel.fund_id == fund_id,
            TransparencyScoreModel.period_start == period_start,
            TransparencyScoreModel.period_end == period_end,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return TransparencyScoreMapper.to_domain(model)

    async def find_history_by_fund_id(
        self, fund_id: str, params: PaginationParams
    ) -> PaginatedItems[TransparencyScore]:
        page = params.page
        page_size = params.page_size
        order = params.order

        if order == "desc":
            order_col = TransparencyScoreModel.created_at.desc()
        else:
            order_col = TransparencyScoreModel.created_at.asc()

        stmt = (
            select(TransparencyScoreModel)
            .where(TransparencyScoreModel.fund_id == fund_id)
            .order_by(order_col)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_stmt = (
            select(func.count())
            .select_from(TransparencyScoreModel)
            .where(TransparencyScoreModel.fund_id == fund_id)
        )

        result = await self._session.execute(stmt)
        count_result = await self._session.execute(count_stmt)
        total_items = count_result.scalar_one()

        items = [TransparencyScoreMapper.to_domain(m) for m in result.scalars().all()]

        return PaginatedItems(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            order=order,
        )
