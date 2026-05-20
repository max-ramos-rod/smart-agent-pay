from datetime import datetime
from pydantic import BaseModel


class SessionCreate(BaseModel):
    delegate_pubkey: str
    ephemeral_private_key: str      # base64, enviado via HTTPS
    session_token_address: str
    spending_limit: float           # USDC
    expiry_days: int


class SessionResponse(BaseModel):
    id: int
    delegate_pubkey: str
    session_token_address: str
    spending_limit: float           # USDC
    expiry: datetime
    created_at: datetime

    class Config:
        from_attributes = True
