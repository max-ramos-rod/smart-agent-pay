from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.responses import success_response
from app.db.session import get_db
from app.schemas.session import SessionCreate
from app.services.session.service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_session_service():
    return SessionService()


@router.post("", status_code=201)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
):
    result = await service.create_session(
        db=db,
        user_id=current_user.id,
        delegate_pubkey=body.delegate_pubkey,
        ephemeral_private_key_b64=body.ephemeral_private_key,
        session_token_address=body.session_token_address,
        spending_limit_usdc=body.spending_limit,
        expiry_days=body.expiry_days,
    )
    await db.commit()
    return success_response(result.model_dump(mode="json"))


@router.get("")
async def get_session(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
):
    result = await service.get_active_session(db, current_user.id)
    if not result:
        return success_response(None)
    return success_response(result.model_dump(mode="json"))


@router.delete("", status_code=204)
async def revoke_session(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
):
    await service.revoke_session(db, current_user.id)
    await db.commit()
