from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    session_key: Mapped[str]
    max_amount: Mapped[float]
    expires_at: Mapped[str]