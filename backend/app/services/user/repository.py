from sqlalchemy import select

from app.core.repositories import SQLAlchemyRepository
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
class UserRepository(SQLAlchemyRepository[User]):
    model = User

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        statement = select(self.model).where(self.model.email == email)
        return await self._get_one(db, statement)