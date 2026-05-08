from fastapi import APIRouter, Depends

from app.services.user.service import UserService
from app.core.pagination import PaginationParams
from app.core.responses import paginated_response, success_response
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

def get_user_service() -> UserService:
    return UserService()

@router.get("")
async def list(
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
) -> dict[str, object]:
    data, meta = await user_service.list(db, params)
    return paginated_response([item.model_dump(mode="json") for item in data], meta)

@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    return success_response((await service.get(db, user_id)).model_dump(mode="json"))

@router.post("", status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    return success_response((await service.create(db, data)).model_dump(mode="json"))

@router.patch("/{user_id}", status_code=200)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    return success_response((await service.update(db, user_id, data)).model_dump(mode="json"))

@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    await service.delete(db, user_id)
    return {"detail": "User deleted"}