from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.services.user.repository import UserRepository
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token

class AuthService:
    def __init__(self, user_repository: UserRepository | None = None):
        self.user_repository = user_repository or UserRepository()

    async def login(self, db: AsyncSession, email: str, password: str):
        user = await self.user_repository.get_user_by_email(db, email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        token = create_access_token(str(user.id))

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    def refresh(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido ou expirado")

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

        user_id = payload["sub"]
        return {
            "access_token": create_access_token(user_id),
            "refresh_token": create_refresh_token(user_id),
        }