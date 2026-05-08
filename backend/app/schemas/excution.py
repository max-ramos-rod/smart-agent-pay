from datetime import datetime
from pydantic import BaseModel

class ExecutionBase(BaseModel):
    strategy_id: int | None = None
    trigger_price: float
    reference_price: float
    drop_percent: float
    amount_sol: float
    status: str
    tx_hash: str | None = None
    explanation: str | None = None

class ExecutionCreate(BaseModel):
    strategy_id: int

class ExecutionResponse(ExecutionBase):
    id: int
    external_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class ExecutionListItemResponse(ExecutionResponse):
    pass