from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import get_current_user
from app.services.wallet.service import WalletService

async def get_current_wallet(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    wallet_address: str = Header(..., alias="X-Wallet-Address"),
):
    return await WalletService().get_user_wallet_by_address(
        db,
        current_user.id,
        wallet_address,
    )