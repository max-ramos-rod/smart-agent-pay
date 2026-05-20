from datetime import datetime, timezone, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.session.repository import SessionRepository
from app.services.session.crypto import encrypt_key, decrypt_key
from app.models.session import Session
from app.schemas.session import SessionResponse


class SessionService:
    def __init__(self, repository: SessionRepository | None = None):
        self.repository = repository or SessionRepository()

    async def create_session(
        self,
        db: AsyncSession,
        user_id: int,
        delegate_pubkey: str,
        ephemeral_private_key_b64: str,
        session_token_address: str,
        spending_limit_usdc: float,
        expiry_days: int,
    ) -> SessionResponse:
        existing = await self.repository.get_by_user(db, user_id)
        if existing:
            await self.repository.delete(db, existing)

        session = Session(
            user_id=user_id,
            delegate_pubkey=delegate_pubkey,
            encrypted_private_key=encrypt_key(ephemeral_private_key_b64),
            session_token_address=session_token_address,
            spending_limit=int(spending_limit_usdc * 1_000_000),  # micro-USDC
            expiry=datetime.now(timezone.utc) + timedelta(days=expiry_days),
        )
        await self.repository.create(db, session)
        return SessionResponse.model_validate(session)

    async def get_active_session(self, db: AsyncSession, user_id: int) -> SessionResponse | None:
        session = await self.repository.get_by_user(db, user_id)
        if not session:
            return None
        if session.expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            await self.repository.delete(db, session)
            return None
        return SessionResponse.model_validate(session)

    async def get_active_session_model(self, db: AsyncSession, user_id: int) -> Session | None:
        """Retorna o ORM model — usado pelo worker para acessar a chave criptografada."""
        session = await self.repository.get_by_user(db, user_id)
        if not session:
            return None
        if session.expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            await self.repository.delete(db, session)
            return None
        return session

    async def revoke_session(self, db: AsyncSession, user_id: int) -> None:
        session = await self.repository.get_by_user(db, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="No active session")
        await self.repository.delete(db, session)

    def get_ephemeral_keypair(self, session: Session):
        from solders.keypair import Keypair
        key_bytes = decrypt_key(session.encrypted_private_key)
        return Keypair.from_bytes(key_bytes)
