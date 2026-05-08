# app/api/v1/routers/executions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.execution.service import ExecutionService
from app.core.pagination import PaginationParams
from app.core.responses import paginated_response, success_response
from app.db.session import get_db
from app.schemas.excution import ExecutionCreate
from app.core.auth import get_current_user
from app.services.wallet.service import WalletService
from app.core.dependencies import get_current_wallet
from app.utils.idempotency import generate_execution_id

router = APIRouter(prefix="/executions", tags=["executions"])

def get_execution_service():
    return ExecutionService()

def get_wallet_service():
    return WalletService()

@router.get("")
async def list_executions(
    wallet = Depends(get_current_wallet),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    service: ExecutionService = Depends(get_execution_service),
):

    data, meta = await service.list(db, wallet.id, params)
    return paginated_response(
        [item.model_dump(mode="json") for item in data],
        meta,
    )