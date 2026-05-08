from datetime import datetime

from pydantic import BaseModel


class StrategyBase(BaseModel):
    type: str
    drop_percent: float
    amount_sol: float
    destination_address: str
    reference_price: float

class StrategyCreate(StrategyBase):
    cooldown_seconds: int = 60
    execution_mode: str = "recurring"

class StrategyUpdate(BaseModel):
    type: str | None = None
    drop_percent: float | None = None
    amount_sol: float | None = None
    destination_address: str | None = None
    reference_price: float | None = None
    active: bool | None = None


class StrategyResponse(StrategyBase):
    id: int
    wallet_id: int
    active: bool
    cooldown_seconds: int
    execution_mode: str
    last_executed_at: datetime | None
    class Config:
        from_attributes = True


class StrategyListItemResponse(StrategyResponse):
    pass