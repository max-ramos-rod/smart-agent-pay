from typing import TypedDict
from app.core.config import settings
import asyncio
from app.services.ai.metrics import calculate_trend, calculate_volatility
# opcional: instale openai>=1.x
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None


class AIDecision(TypedDict):
    execute: bool
    confidence: float
    reason: str


class AIAgent:
    async def evaluate(self, strategy, price: float, history: list[float]) -> AIDecision:
        drop = ((strategy.reference_price - price) / strategy.reference_price) * 100
        # 🔥 filtro base (evita custo)
        if drop < (strategy.drop_percent * 0.5):
            return {
                "execute": False,
                "confidence": 0.1,
                "reason": f"Filtro base: drop muito pequeno ({drop:.2f}%)"
            }

        if len(history) < 5:
            return self._heuristic(strategy, price)
        
        trend = calculate_trend(history)
        volatility = calculate_volatility(history)

        # 🔥 inteligência local primeiro
        if trend < -0.5:
            return {
                "execute": False,
                "confidence": 0.3,
                "reason": f"Queda forte (trend={trend:.4f})"
            }

        if volatility > 0.15:
            return {
                "execute": False,
                "confidence": 0.4,
                "reason": f"Alta volatilidade ({volatility:.4f})"
            }

        # 🔁 agora decide se chama OpenAI
        if not settings.USE_AI or not client:
            return self._heuristic(strategy, price)

        try:
            return await asyncio.wait_for(
                self._openai_decision(strategy, price, history, trend, volatility),
                timeout=settings.AI_TIMEOUT_SECONDS,
            )
        except Exception as e:
            print(f"⚠️ AI fallback: {e}")
            return self._heuristic(strategy, price)

    def _heuristic(self, strategy, price: float) -> AIDecision:
        drop = ((strategy.reference_price - price) / strategy.reference_price) * 100
        if drop >= strategy.drop_percent:
            return {
                "execute": True,
                "confidence": min(drop / max(strategy.drop_percent, 0.0001), 1.0),
                "reason": f"Heurística: drop {drop:.2f}% >= {strategy.drop_percent}%",
            }
        return {
            "execute": False,
            "confidence": 0.2,
            "reason": f"Heurística: drop insuficiente {drop:.2f}%",
        }

    async def _openai_decision(self, strategy, price, history, trend, volatility):
        drop = ((strategy.reference_price - price) / strategy.reference_price) * 100

        history_str = ", ".join([f"{p:.2f}" for p in history[-10:]])

        system = (
            "Você é um agente de execução de ordens em criptomoedas. "
            "Sua função é decidir se deve executar uma ordem de COMPRA NA QUEDA (buy the dip). "
            "A estratégia JÁ FOI configurada pelo usuário para disparar quando o preço cair X%. "
            "Você deve aprovar se a queda atingiu o alvo e não há sinal de queda livre contínua. "
            "Responda apenas JSON."
        )

        user = f"""
        Estratégia: comprar {strategy.amount_sol} SOL quando o preço cair {strategy.drop_percent}%.
        Preço de referência: {strategy.reference_price:.2f}
        Preço atual: {price:.2f}
        Queda atual: {drop:.2f}% (alvo: {strategy.drop_percent}%)
        Histórico recente (últimos 10 preços): [{history_str}]
        Tendência: {trend:.4f} (positivo = recuperando, negativo = ainda caindo)
        Volatilidade: {volatility:.4f}

        A queda atingiu o alvo configurado pelo usuário. Deve executar a compra?
        Recuse apenas se houver queda livre contínua (tendência muito negativa) ou volatilidade extrema.
        JSON: {{"execute": true/false, "confidence": 0.0-1.0, "reason": "..."}}
        """

        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
        )

        import json
        parsed = json.loads(resp.choices[0].message.content)

        return {
            "execute": bool(parsed.get("execute", False)),
            "confidence": float(parsed.get("confidence", 0)),
            "reason": parsed.get("reason", ""),
        }