# app/models/strategy.py
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy import DateTime
from app.db.base import Base

class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(primary_key=True)

    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False
    )

    type: Mapped[str] = mapped_column(String(50), nullable=False)

    drop_percent: Mapped[float] = mapped_column(Float, nullable=False)
    amount_sol: Mapped[float] = mapped_column(Float, nullable=False)
    destination_address: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_price: Mapped[float] = mapped_column(Float, nullable=False)

    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    last_executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    cooldown_seconds: Mapped[int] = mapped_column(default=60)
    execution_mode: Mapped[str] = mapped_column(default="recurring")  # "once" | "recurring"
    token: Mapped[str] = mapped_column(String(10), default="SOL")
    amount_usdc: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # relationships
    wallet = relationship("Wallet", back_populates="strategies")
    executions = relationship("Execution", back_populates="strategy")