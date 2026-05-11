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
    token: str = "SOL"
    amount_usdc: float | None = None
    # swap via Jupiter
    token_in: str | None = None
    token_out: str | None = None
    slippage_bps: int | None = 50

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
    token: str = "SOL"
    amount_usdc: float | None = None
    token_in: str | None = None
    token_out: str | None = None
    slippage_bps: int | None = None
    last_executed_at: datetime | None
    class Config:
        from_attributes = True


class StrategyListItemResponse(StrategyResponse):
    pass