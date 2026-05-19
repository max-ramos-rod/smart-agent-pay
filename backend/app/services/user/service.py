# services/user/service.py — correção do bug update_data usado antes de ser definido

from app.services.user.repository import UserRepository
from fastapi import HTTPException
from app.core.pagination import PaginationMetaBuilder, PaginationParams
from app.schemas.user import UserCreate, UserListItemResponse, UserResponse, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password

class UserService:
    def __init__(self, repository: UserRepository | None = None) -> None:
        self.repository = repository or UserRepository()

    async def list(self, db: AsyncSession, params: PaginationParams):
        items, total = await self.repository.list_paginated(db, params)
        meta = PaginationMetaBuilder.build(total, params)
        return ([UserListItemResponse.model_validate(item) for item in items], meta)

    async def get(self, db: AsyncSession, user_id: int) -> UserResponse:
        user = await self.repository.get(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse.model_validate(user)

    async def create(self, db: AsyncSession, data: UserCreate) -> UserResponse:
        user_data = data.model_dump()
        user_data["email"] = user_data["email"].lower().strip()
        user_data["password_hash"] = hash_password(user_data.pop("password"))
        existing = await self.repository.get_by_email(db, user_data["email"])
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        user = self.repository.model(**user_data)
        await self.repository.create(db, user)
        return UserResponse.model_validate(user)

    async def update(self, db: AsyncSession, user_id: int, data: UserUpdate) -> UserResponse:
        user = await self.repository.get(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # CORRIGIDO: update_data definido ANTES de ser usado
        update_data = data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))
        await self.repository.update_fields(db, user, update_data)
        return UserResponse.model_validate(user)

    async def delete(self, db: AsyncSession, user_id: int) -> None:
        user = await self.repository.get(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await self.repository.delete(db, user)
