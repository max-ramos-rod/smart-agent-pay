from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.execution.repository import ExecutionRepository
from app.services.strategy.repository import StrategyRepository
from app.models.enums import ExecutionStatus

from app.core.pagination import PaginationParams, PaginationMetaBuilder
from app.schemas.excution import ExecutionCreate, ExecutionListItemResponse, ExecutionResponse


class ExecutionService:
    def __init__(
        self,
        repository: ExecutionRepository | None = None,
        strategy_repository: StrategyRepository | None = None,
    ):
        self.repository = repository or ExecutionRepository()
        self.strategy_repository = strategy_repository or StrategyRepository()

    async def list(
        self,
        db: AsyncSession,
        wallet_id: int,
        params: PaginationParams,
    ):
        items, total = await self.repository.list_by_wallet(db, wallet_id, params)
        meta = PaginationMetaBuilder.build(total, params)

        return (
            [ExecutionListItemResponse.model_validate(i) for i in items],
            meta,
        )

    async def create_from_strategy(
        self,
        db: AsyncSession,
        strategy_id: int,
        wallet_id: int,
        external_id: str,
    ):
        strategy = await self.strategy_repository.get(db, strategy_id)

        if not strategy or strategy.wallet_id != wallet_id:
            raise HTTPException(status_code=404, detail="Strategy not found")

        execution = self.repository.model(
            wallet_id=strategy.wallet_id,
            strategy_id=strategy.id,
            trigger_price=strategy.reference_price,  # placeholder
            reference_price=strategy.reference_price,
            drop_percent=strategy.drop_percent,
            amount_sol=strategy.amount_sol,
            status=ExecutionStatus.PENDING,
            external_id=external_id,
        )

        await self.repository.create(db, execution)

        return ExecutionResponse.model_validate(execution)
    
    async def create(
        self,
        db: AsyncSession,
        wallet_id: int,
        strategy_id: int | None,
        data: ExecutionCreate,
    ):
        execution = self.repository.model(
            wallet_id=wallet_id,
            strategy_id=strategy_id,
            trigger_price=data.trigger_price,
            reference_price=data.reference_price,
            drop_percent=data.drop_percent,
            amount_sol=data.amount_sol,
            status=data.status,
            tx_hash=data.tx_hash,
            explanation=data.explanation,
        )

        await self.repository.create(db, execution)
        return ExecutionResponse.model_validate(execution)
    
    async def exists_by_external_id(
        self,
        db: AsyncSession,
        external_id: str,
    ) -> bool:
        return await self.repository.exists_by_external_id(db, external_id)

    async def create_completed_execution(
        self,
        db: AsyncSession,
        strategy_id: int,
        wallet_id: int,
        external_id: str,
        tx_hash: str,
    ):
        strategy = await self.strategy_repository.get(db, strategy_id)

        execution = self.repository.model(
            wallet_id=wallet_id,
            strategy_id=strategy.id,
            trigger_price=strategy.reference_price,
            reference_price=strategy.reference_price,
            drop_percent=strategy.drop_percent,
            amount_sol=strategy.amount_sol,
            status=ExecutionStatus.SUCCESS,
            tx_hash=tx_hash,
            external_id=external_id,
        )

        await self.repository.create(db, execution)

        return ExecutionResponse.model_validate(execution)
    
    async def create_failed_execution(
        self,
        db: AsyncSession,
        strategy_id: int,
        wallet_id: int,
        external_id: str,
        explanation: str,
    ):
        strategy = await self.strategy_repository.get(db, strategy_id)

        execution = self.repository.model(
            wallet_id=wallet_id,
            strategy_id=strategy.id,
            trigger_price=strategy.reference_price,
            reference_price=strategy.reference_price,
            drop_percent=strategy.drop_percent,
            amount_sol=strategy.amount_sol,
            status=ExecutionStatus.FAILED,
            explanation=explanation,
            external_id=external_id,
        )

        await self.repository.create(db, execution)

        return ExecutionResponse.model_validate(execution)