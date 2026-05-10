# strategy_runner.py — versão corrigida
# Problemas corrigidos:
# 1. price_history movido para fora do loop (sobrevive entre iterações, mas ainda perde em restart)
# 2. get_price() usa CoinGecko + override do demo endpoint
# 3. import corrigido do generate_execution_id

import time
import json
import asyncio
import httpx
from collections import deque
from datetime import datetime, timezone

from app.db.session import AsyncSessionLocal
from app.services.strategy.service import StrategyService
from app.services.execution.service import ExecutionService
from app.services.solana.service import SolanaService
from app.utils.idempotency import generate_execution_id
from app.utils.logging import log_agent_execution
from app.services.ai.agent import AIAgent

from solders.keypair import Keypair
from app.core.config import settings

# price_history FORA do loop — sobrevive entre iterações do while True
_price_history: deque = deque(maxlen=20)

# referência ao override do demo (importado do endpoint)
def _get_override():
    try:
        from app.api.v1.routers.demo import get_demo_price
        return get_demo_price()
    except ImportError:
        return None

_price_cache: dict = {"value": None, "ts": 0}

async def get_price() -> float:
    override = _get_override()
    if override is not None:
        return override

    # usa cache se tiver menos de 30s
    now = time.time()
    if _price_cache["value"] and (now - _price_cache["ts"]) < 30:
        return _price_cache["value"]

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "solana", "vs_currencies": "usd"},
            )
            data = r.json()
            # verifica se veio erro antes de usar
            if "solana" not in data:
                raise ValueError(f"CoinGecko error: {data}")
            price = float(data["solana"]["usd"])
            _price_cache["value"] = price
            _price_cache["ts"] = now
            return price
    except Exception:
        return _price_cache["value"] or (_price_history[-1] if _price_history else 150.0)

async def run_strategies():
    print("🚀 Worker iniciado")
    ai_agent = AIAgent()

    solana_service = SolanaService()
    private_key = json.loads(settings.SOLANA_PRIVATE_KEY)
    agent_keypair = Keypair.from_bytes(bytes(private_key))

    strategy_service = StrategyService()
    execution_service = ExecutionService()

    while True:
        async with AsyncSessionLocal() as db:
            try:

                strategies = await strategy_service.list_active(db)
                price = await get_price()

                _price_history.append(price)
                history = list(_price_history)

                print(f"📊 Preço: {price:.2f} | histórico: {len(history)} pts")

                now = datetime.now(timezone.utc)

                for s in strategies:
                    drop = ((s.reference_price - price) / s.reference_price) * 100

                    if drop < (s.drop_percent * 0.5):
                        continue

                    if s.last_executed_at:
                        last = s.last_executed_at
                        if last.tzinfo is None:
                            last = last.replace(tzinfo=timezone.utc)
                        if (now - last).total_seconds() < s.cooldown_seconds:
                            print(f"⏳ Cooldown ativo (strategy {s.id})")
                            continue

                    decision = await ai_agent.evaluate(s, price, history)

                    print(
                        f"🧠 AI (strategy {s.id}): execute={decision['execute']} | {decision['reason']}"
                    )

                    if not decision["execute"]:
                        log_agent_execution(
                            user_id=s.wallet.user_id,
                            status="skipped",
                            metadata={"strategy_id": s.id, "price": price, "reason": decision["reason"]},
                        )
                        continue

                    execution_id = generate_execution_id(s.id, price)

                    exists = await execution_service.exists_by_external_id(db, execution_id)
                    if exists:
                        print("⏭️ Idempotência: já executado nesta janela, pulando")
                        continue


                    try:
                        if s.token == "USDC":
                            tx_hash = await solana_service.transfer_usdc(
                                from_keypair=agent_keypair,
                                to_pubkey=s.destination_address,
                                amount_usdc=s.amount_usdc or 0,
                            )
                        else:
                            tx_hash = await solana_service.transfer_sol(
                                from_keypair=agent_keypair,
                                to_pubkey=s.destination_address,
                                amount_sol=s.amount_sol,
                            )

                        await execution_service.create_completed_execution(
                            db=db,
                            strategy_id=s.id,
                            wallet_id=s.wallet_id,
                            external_id=execution_id,
                            tx_hash=tx_hash,
                            trigger_price=price,
                        )

                        print(f"✅ {s.token} TX enviada: {tx_hash}")

                    except Exception as e:
                        await execution_service.create_failed_execution(
                            db=db,
                            strategy_id=s.id,
                            wallet_id=s.wallet_id,
                            external_id=execution_id,
                            explanation=str(e),
                            trigger_price=price,
                        )

                        print(f"❌ Erro {s.token}: {e}")

                    await db.flush()

                    s.last_executed_at = now
                    if s.execution_mode == "once":
                        s.active = False

                    log_agent_execution(
                        user_id=s.wallet.user_id,
                        status="executed",
                        metadata={
                            "strategy_id": s.id,
                            "price": price,
                            "confidence": decision["confidence"],
                            "reason": decision["reason"],
                        },
                    )

                await db.commit()

            except Exception as e:
                await db.rollback()
                print("❌ Worker error:", e)

        await asyncio.sleep(5)
