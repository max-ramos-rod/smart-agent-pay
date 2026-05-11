from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.wallet.service import WalletService
from app.core.auth import get_current_user
from app.core.responses import success_response
from fastapi import Header
from app.core.dependencies import get_current_wallet

router = APIRouter(prefix="/wallets", tags=["wallets"])

def get_wallet_service():
     return WalletService()

@router.get("/balance")
async def get_balance(
    wallet = Depends(get_current_wallet),
    service: WalletService = Depends(get_wallet_service),
):
    return await service.get_balance(wallet.public_key)

@router.get("/balances")
async def get_balances(
    wallet = Depends(get_current_wallet),
    service: WalletService = Depends(get_wallet_service),
):
    return await service.get_all_balances(wallet.public_key)

@router.post("/connect")
async def connect_wallet(
    public_key: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = get_wallet_service()
    wallet = await service.connect_wallet(db, current_user.id, public_key)
    return success_response({
        "id": wallet.id,
        "public_key": wallet.public_key
    })