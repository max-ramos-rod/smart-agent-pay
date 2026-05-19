# app/api/routes/demo.py
# Endpoint apenas para demo — remover em produção
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.workers.strategy_runner import get_price

router = APIRouter(prefix="/demo", tags=["demo"])

# Preço global sobrescrito pelo apresentador
_override_price: float | None = None

class PriceOverride(BaseModel):
    price: float

@router.post("/set-price")
async def set_demo_price(body: PriceOverride):
    global _override_price
    _override_price = body.price
    return {"ok": True, "price": body.price}

@router.delete("/set-price")
async def clear_demo_price():
    global _override_price
    _override_price = None
    return {"ok": True}

def get_demo_price() -> float | None:
    return _override_price

@router.get("/price")
async def current_price():
    return {"price": await get_price()}
