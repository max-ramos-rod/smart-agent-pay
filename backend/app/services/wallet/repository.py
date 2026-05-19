from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories import SQLAlchemyRepository
from app.models.wallet import Wallet


class WalletRepository(SQLAlchemyRepository[Wallet]):
    model = Wallet

    async def get_by_public_key(self, db: AsyncSession, public_key: str) -> Wallet | None:
        stmt = select(self.model).where(self.model.public_key == public_key)
        return await self._get_one(db, stmt)

    async def get_by_user(self, db: AsyncSession, user_id: int):
        stmt = select(self.model).where(self.model.user_id == user_id)
        return await self._list_from_stmt(db, stmt)