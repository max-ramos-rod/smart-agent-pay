# models/execution.py — versão corrigida
# Problema: ExecutionStatus definido localmente E importado de enums — duplicata
# Correção: remover definição local, usar só o import

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, String, DateTime, ForeignKey
from app.db.base import Base

class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(primary_key=True)

    strategy_id: Mapped[int | None] = mapped_column(
        ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True
    )
    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )

    trigger_price: Mapped[float] = mapped_column(Float, nullable=False)
    reference_price: Mapped[float] = mapped_column(Float, nullable=False)
    drop_percent: Mapped[float] = mapped_column(Float, nullable=False)
    amount_sol: Mapped[float] = mapped_column(Float, nullable=False)

    token: Mapped[str] = mapped_column(String(10), default="SOL")
    amount_usdc: Mapped[float | None] = mapped_column(Float, nullable=True)

    tx_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    explanation: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    strategy = relationship("Strategy", back_populates="executions")
    wallet = relationship("Wallet", back_populates="executions")
