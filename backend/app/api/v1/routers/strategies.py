from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.strategy.service import StrategyService
from app.schemas.strategy import StrategyCreate, StrategyUpdate
from app.core.pagination import PaginationParams
from app.core.responses import paginated_response, success_response
from app.db.session import get_db
from app.core.auth import get_current_user
from app.services.wallet.service import WalletService
from app.core.dependencies import get_current_wallet

router = APIRouter(prefix="/strategies", tags=["strategies"])

def get_strategy_service():
    return StrategyService()

def get_wallet_service():
    return WalletService()

@router.get("")
async def list_strategies(
    wallet = Depends(get_current_wallet),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    service: StrategyService = Depends(get_strategy_service),
):
    data, meta = await service.list(db, wallet.id, params)
    return paginated_response(
        [item.model_dump(mode="json") for item in data],
        meta
    )

@router.get("/{strategy_id}")
async def get_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
    service: StrategyService = Depends(get_strategy_service),
    wallet_service: WalletService = Depends(get_wallet_service),
    current_user=Depends(get_current_user),
):
    wallet = await wallet_service.get_user_wallet(db, current_user.id)
    result = await service.get(db, wallet.id, strategy_id)
    return success_response(result.model_dump(mode="json"))

@router.post("", status_code=201)
async def create_strategy(
    data: StrategyCreate,
    db: AsyncSession = Depends(get_db),
    service: StrategyService = Depends(get_strategy_service),
    wallet_service: WalletService = Depends(get_wallet_service),
    current_user=Depends(get_current_user)
):
    wallet = await wallet_service.get_user_wallet(db, current_user.id)

    result = await service.create(
        db,
        wallet_id=wallet.id,
        data=data,
    )

    return success_response(result.model_dump(mode="json"))

@router.patch("/{strategy_id}")
async def update_strategy(
    strategy_id: int,
    data: StrategyUpdate,
    db: AsyncSession = Depends(get_db),
    service: StrategyService = Depends(get_strategy_service),
    wallet_service: WalletService = Depends(get_wallet_service),
    current_user=Depends(get_current_user),
):
    wallet = await wallet_service.get_user_wallet(db, current_user.id)
    result = await service.update(db, wallet.id, strategy_id, data)
    return success_response(result.model_dump(mode="json"))

@router.delete("/{strategy_id}", status_code=204)
async def delete_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
    service: StrategyService = Depends(get_strategy_service),
    wallet_service: WalletService = Depends(get_wallet_service),
    current_user=Depends(get_current_user),
):
    wallet = await wallet_service.get_user_wallet(db, current_user.id)
    await service.delete(db, wallet.id, strategy_id)