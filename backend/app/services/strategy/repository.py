from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.strategy import Strategy
from app.core.repositories import SQLAlchemyRepository
from app.core.pagination import PaginationParams


class StrategyRepository(SQLAlchemyRepository[Strategy]):
    model = Strategy

    async def list_by_wallet(
        self,
        db: AsyncSession,
        wallet_id: int,
        params: PaginationParams,
    ):
        stmt = select(self.model).where(self.model.wallet_id == wallet_id)
        return await self._paginate_select(db, stmt, params)

    async def get_by_wallet_and_id(
        self,
        db: AsyncSession,
        wallet_id: int,
        strategy_id: int,
    ):
        stmt = select(self.model).where(
            self.model.id == strategy_id,
            self.model.wallet_id == wallet_id,
        )
        return await self._get_one(db, stmt)

    async def list_active(self, db: AsyncSession):
        stmt = (
            select(self.model)
            .options(joinedload(self.model.wallet))
            .where(self.model.active.is_(True))
        )
        return await self._list_from_stmt(db, stmt)        