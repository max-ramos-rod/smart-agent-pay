from fastapi import APIRouter
from datetime import datetime, timedelta
import secrets

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/session")
async def create_session():
    return {
        "session_key": secrets.token_hex(32),
        "max_amount": 100,
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }


@router.get("/logs")
async def get_logs():
    return [
        {
            "id": 1,
            "action": "BUY",
            "amount_sol": 10,
            "trigger_price": 95,
            "explanation": "Price dropped 5% from reference",
            "status": "success",
            "tx_hash": "mock_tx_hash",
            "created_at": datetime.utcnow() - timedelta(minutes=30)
        }
    ]

@router.post("/logs")
async def create_log(data: dict):
    log = {
        "id": 1,  # depois vira auto increment
        "action": data.get("action"),
        "amount_sol": data.get("amount_sol"),
        "trigger_price": data.get("trigger_price"),
        "reference_price": data.get("reference_price"),
        "drop_percent": data.get("drop_percent"),
        "status": data.get("status"),
        "tx_hash": data.get("tx_hash"),
        "explanation": data.get("explanation"),
        "created_at": datetime.utcnow(),
    }

    return log