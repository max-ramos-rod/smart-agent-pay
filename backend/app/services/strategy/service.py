from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.strategy.repository import StrategyRepository
from app.schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListItemResponse,
)
from app.core.pagination import PaginationParams, PaginationMetaBuilder
from sqlalchemy.orm import joinedload
from app.models.strategy import Strategy
class StrategyService:
    def __init__(self, repository: StrategyRepository | None = None):
        self.repository = repository or StrategyRepository()

    async def list(self, db: AsyncSession, wallet_id: int, params: PaginationParams):
        items, total = await self.repository.list_by_wallet(
            db, wallet_id, params
        )

        meta = PaginationMetaBuilder.build(total, params)

        return (
            [StrategyListItemResponse.model_validate(i) for i in items],
            meta,
        )

    async def get(self, db: AsyncSession, wallet_id: int, strategy_id: int):
        strategy = await self.repository.get_by_wallet_and_id(
            db, wallet_id, strategy_id
        )

        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        return StrategyResponse.model_validate(strategy)

    async def create(self, db: AsyncSession, wallet_id: int, data: StrategyCreate):
        strategy = self.repository.model(
            wallet_id=wallet_id,
            type=data.type,
            drop_percent=data.drop_percent,
            amount_sol=data.amount_sol,
            destination_address=data.destination_address,
            reference_price=data.reference_price,
            cooldown_seconds=data.cooldown_seconds,
            execution_mode=data.execution_mode,
            token=data.token,
            amount_usdc=data.amount_usdc,
            token_in=data.token_in,
            token_out=data.token_out,
            slippage_bps=data.slippage_bps,
        )        

        await self.repository.create(db, strategy)
        return StrategyResponse.model_validate(strategy)

    async def update(
        self,
        db: AsyncSession,
        wallet_id: int,
        strategy_id: int,
        data: StrategyUpdate,
    ):
        strategy = await self.repository.get_by_wallet_and_id(
            db, wallet_id, strategy_id
        )

        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        update_data = data.model_dump(exclude_unset=True)

        await self.repository.update_fields(db, strategy, update_data)

        return StrategyResponse.model_validate(strategy)

    async def delete(self, db: AsyncSession, wallet_id: int, strategy_id: int):
        strategy = await self.repository.get_by_wallet_and_id(
            db, wallet_id, strategy_id
        )

        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        await self.repository.delete(db, strategy)

    async def list_active(self, db: AsyncSession):
        return await self.repository.list_active(db)   