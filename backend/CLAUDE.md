# CLAUDE.md — Backend

FastAPI backend for SentinelFi. Handles authentication, strategy management, execution logging, and the background worker that monitors Solana prices and triggers on-chain actions.

## Stack

- **FastAPI** (async) + **SQLAlchemy 2** (async) + **PostgreSQL 17**
- **Alembic** for migrations
- **Pydantic v2** schemas
- **solders** + **solana-py** for Solana interactions
- **httpx** for async HTTP (CoinGecko, Jupiter API)
- **openai** SDK (optional, gpt-4o-mini)

## Running locally

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

## Layer Pattern

All routes follow: **Router → Service → Repository → DB**

```
app/
  api/v1/routers/   — HTTP endpoints, request/response shapes
  services/         — business logic
  models/           — SQLAlchemy ORM models (db tables)
  schemas/          — Pydantic v2 input/output shapes
  workers/          — background tasks started on app startup
  core/             — config, auth, database, dependencies
  utils/            — idempotency, logging helpers
```

All responses use the envelope: `{ "data": {...}, "meta": {...} }`

## Key Files

| File | Purpose |
|------|---------|
| `app/workers/strategy_runner.py` | Core loop: polls CoinGecko every 5s, evaluates AI, bifurcates on `strategy.type`, creates executions |
| `app/services/jupiter/service.py` | Jupiter API v6 — quote, swap TX, mock fallback |
| `app/services/ai/agent.py` | AI evaluation pipeline: base filter → local heuristics → OpenAI → fallback |
| `app/services/ai/metrics.py` | `calculate_trend()`, `calculate_volatility()` for price history |
| `app/services/solana/service.py` | SOL / USDC transfer signing with agent keypair |
| `app/services/execution/service.py` | `create_awaiting_signature()`, `create_awaiting_swap()`, expiry logic |
| `app/api/v1/routers/demo.py` | `POST /demo/override-price` — inject fake price for testing |
| `scripts/gera_token.py` | Generate JWT for manual API testing |
| `scripts/reset_executions.py` | Wipe execution records in DB |

## Strategy Types

The `strategy.type` field drives worker bifurcation:

- `transfer` — worker builds `awaiting_signature` execution; user signs SOL/USDC transfer via Phantom
- `swap` — worker gets Jupiter quote + swap TX; builds `awaiting_swap` execution; user signs `VersionedTransaction` via Phantom

## Execution Statuses

| status | meaning |
|--------|---------|
| `awaiting_signature` | SOL/USDC transfer pending Phantom signature |
| `awaiting_swap` | Jupiter swap pending Phantom signature |
| `completed` | TX confirmed on-chain |
| `expired` | pending >3 min, auto-expired by worker |
| `skipped` | AI/heuristic rejected execution |

## Jupiter Mock Mode

Jupiter API v6 is mainnet-only. In devnet:
1. `get_quote_safe()` catches failures → returns `None`
2. `mock_quote()` generates fake quote (`_mock: True`)
3. `serialized_tx` is stored as `None` on the execution
4. Frontend detects mock and confirms without real Phantom interaction

## AI Agent Pipeline (`app/services/ai/agent.py`)

1. **Base filter** — drop < 50% of target → skip (no AI cost)
2. **Trend check** — `trend < -0.5` → reject (sharp freefall)
3. **Volatility check** — `volatility > 0.15` → reject (extreme swings)
4. **OpenAI** (if `USE_AI=true`, history ≥ 5 points) — gpt-4o-mini with buy-the-dip context
5. **Fallback heuristic** — simple drop ≥ target comparison

## Models

### Strategy

```python
type: str                  # "transfer" | "swap"
drop_percent: float
amount_sol: float
destination_address: str
reference_price: float
active: bool
cooldown_seconds: int      # default 60
execution_mode: str        # "once" | "recurring"
token: str                 # "SOL" | "USDC"
amount_usdc: float | None
token_in: str | None       # swap only
token_out: str | None      # swap only
slippage_bps: int | None   # swap only, e.g. 50 = 0.5%
last_executed_at: datetime | None
```

### Execution

```python
strategy_id: int | None
wallet_id: int
trigger_price: float
reference_price: float
drop_percent: float
amount_sol: float
token: str
amount_usdc: float | None
serialized_tx: Text | None   # base64 Jupiter VersionedTransaction
tx_hash: str | None
status: str
explanation: str | None
external_id: str | None      # unique idempotency key
created_at: datetime
```

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
SECRET_KEY=<jwt-signing-key>
SOLANA_PRIVATE_KEY=[...]            # JSON byte array, agent keypair
OPENAI_API_KEY=<key>               # optional
USE_AI=false                       # true to enable OpenAI gating
AI_TIMEOUT_SECONDS=5
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=["http://localhost:8080"]
```

## Database Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

Migration files: `alembic/versions/`

## Auth

- Phantom wallet signs a message → backend verifies signature → issues JWT
- Short-lived access token (60 min) + long-lived refresh token (7 days)
- Both are stateless JWTs with `type` claim (`"access"` / `"refresh"`)
- Frontend auto-refreshes via `POST /api/v1/auth/refresh` on 401

## Key Design Decisions

- **Single-worker**: `strategy_runner` is designed for one Uvicorn worker. Multi-worker would need Redis-backed locking.
- **Idempotency**: `external_id` is a deterministic hash of `(strategy_id, price_window)`; unique DB constraint prevents double execution.
- **Price caching**: CoinGecko cached 30s in-process; falls back to last known price on error.
- **Agent keypair**: used only for SOL/USDC transfers. Jupiter swaps are signed by the user's Phantom wallet directly.
