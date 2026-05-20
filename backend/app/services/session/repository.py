from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories import SQLAlchemyRepository
from app.models.session import Session


class SessionRepository(SQLAlchemyRepository[Session]):
    model = Session

    async def get_by_user(self, db: AsyncSession, user_id: int) -> Session | None:
        stmt = select(self.model).where(self.model.user_id == user_id)
        return await self._get_one(db, stmt)
