from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime, BigInteger

from app.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # um usuário tem no máximo uma sessão ativa
    )

    delegate_pubkey: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_private_key: Mapped[str] = mapped_column(String(512), nullable=False)
    session_token_address: Mapped[str] = mapped_column(String(255), nullable=False)
    spending_limit: Mapped[int] = mapped_column(BigInteger, nullable=False)  # micro-USDC
    expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="session")
