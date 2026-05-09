from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth.service import AuthService
from app.db.session import get_db
from datetime import datetime
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from app.services.wallet.service import WalletService
from app.services.user.service import UserService
from app.core.security import create_access_token, create_refresh_token

import base58
import base64
import secrets

from app.schemas.auth import WalletLoginRequest, RefreshRequest
from app.schemas.user import UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])

def get_user_service():
    return AuthService()

challenge_store = {}

@router.get("/challenge")
async def get_challenge(public_key: str):
    nonce = secrets.token_hex(16)
    message = f"Login at {datetime.utcnow().isoformat()} | nonce: {nonce}"
    challenge_store[public_key] = message
    return {"message": message}

@router.post("/login")
async def login(
    data: WalletLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    public_key = data.public_key
    signature = data.signature
    message = data.message
    
    stored_message = challenge_store.get(public_key)

    if not stored_message or stored_message != message:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid challenge")

    try:
        verify_key = VerifyKey(base58.b58decode(public_key))
        verify_key.verify(message.encode(), base64.b64decode(signature))
    except BadSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    wallet_service = WalletService()
    user_service = UserService()

    wallet = await wallet_service.repository.get_by_public_key(db, public_key)

    if not wallet:
        user = await user_service.create(
            db,
            UserCreate(
                name="Wallet User",
                email=f"{public_key}@smartagent.pay",
                password="dummy",
            )
        )

        wallet = await wallet_service.connect_wallet(
            db,
            user_id=user.id,
            public_key=public_key,
        )

    user_id = str(wallet.user_id)
    token = create_access_token(user_id)
    refresh = create_refresh_token(user_id)

    return {
        "access_token": token,
        "refresh_token": refresh,
        "wallet_id": wallet.id,
    }


@router.post("/refresh")
async def refresh_token(data: RefreshRequest):
    return AuthService().refresh(data.refresh_token)