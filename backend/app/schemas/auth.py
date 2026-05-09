from pydantic import BaseModel

class WalletLoginRequest(BaseModel):
    public_key: str
    signature: str
    message: str

class RefreshRequest(BaseModel):
    refresh_token: str