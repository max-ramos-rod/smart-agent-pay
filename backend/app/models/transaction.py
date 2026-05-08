from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    type: Mapped[str]
    amount: Mapped[float]
    asset: Mapped[str]
    status: Mapped[str]
    tx_hash: Mapped[str]