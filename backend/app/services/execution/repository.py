# app/services/execution/repository.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution import Execution
from app.core.repositories import SQLAlchemyRepository
from app.core.pagination import PaginationParams


class ExecutionRepository(SQLAlchemyRepository[Execution]):
    model = Execution

    async def list_by_wallet(
        self,
        db: AsyncSession,
        wallet_id: int,
        params: PaginationParams,
    ):
        stmt = (
            select(self.model)
            .where(self.model.wallet_id == wallet_id)
            .order_by(self.model.created_at.desc())
        )

        return await self._paginate_select(db, stmt, params)

    async def exists_by_external_id(self, db, external_id: str) -> bool:
        stmt = select(self.model).where(self.model.external_id == external_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def has_pending_signature(self, db, strategy_id: int) -> bool:
        stmt = select(self.model).where(
            self.model.strategy_id == strategy_id,
            self.model.status == "awaiting_signature",
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None