# CLAUDE.md — Backend

FastAPI backend for SentinelFi. Handles authentication, strategy management, execution logging, and the background worker that monitors Solana prices and creates pending executions.

## Stack

- **FastAPI** (async) + **SQLAlchemy 2** (async) + **PostgreSQL 17**
- **Alembic** for migrations
- **Pydantic v2** schemas
- **solders** + **solana-py** for Solana transaction construction
- **httpx** for async HTTP (CoinGecko, Jupiter API)
- **openai** SDK (optional, gpt-4o-mini)

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
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
| `app/services/solana/service.py` | SOL / USDC transfer construction (accepts ephemeral keypair from user session) |
| `app/services/execution/service.py` | `create_awaiting_signature()`, `create_awaiting_swap()`, expiry logic |
| `app/api/v1/routers/sessions.py` | Session key management — POST/GET/DELETE |
| `app/api/v1/routers/demo.py` | `POST /demo/override-price` — inject fake price for testing |
| `scripts/gera_token.py` | Generate JWT for manual API testing |
| `scripts/reset_executions.py` | Wipe execution records in DB |

## Strategy Types

The `strategy.type` field drives worker bifurcation:

- `transfer` — worker builds `awaiting_signature` execution; user signs SOL/USDC transfer via Phantom (or agent signs autonomously if session active)
- `swap` — worker gets Jupiter quote + swap TX; builds `awaiting_swap` execution; user signs `VersionedTransaction` via Phantom (or agent signs if session active)

## Execution Statuses

| status | meaning |
|--------|---------|
| `awaiting_signature` | SOL/USDC transfer pending Phantom signature |
| `awaiting_swap` | Jupiter swap pending Phantom signature |
| `completed` | TX confirmed on-chain |
| `expired` | pending >3 min, auto-expired by worker |
| `skipped` | AI/heuristic rejected execution |

## Session Keys

Each user generates an ephemeral keypair client-side. They sign once via Phantom creating an on-chain `SessionToken(owner, delegate, spending_limit, expiry)`. The backend stores the encrypted ephemeral private key per user. When a strategy triggers and an active session exists, the worker signs autonomously using that user's ephemeral key — no Phantom interaction needed.

**There is no shared server keypair.** Each session key is scoped to a single user, has a spending limit, and expires automatically.

### Sessions model (`app/models/session.py`)

```python
user_id: int                 # FK to users, unique (one session per user)
delegate_pubkey: str         # ephemeral pubkey (on-chain delegate)
encrypted_private_key: str   # AES-encrypted ephemeral private key (Fernet)
spending_limit: int          # micro-USDC (spending_limit_usdc * 1_000_000)
expiry: datetime             # session expiry (UTC)
session_token_address: str   # on-chain SessionToken PDA address
```

Migration was applied in `alembic/versions/6e84c397014c_add_sessions_table.py`.

Worker uses `session_service.get_active_session_model(db, user_id)` (returns ORM) to decrypt the key. Router uses `get_active_session(db, user_id)` (returns Pydantic schema).

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

### Current limitations

- Price history is an in-memory `deque(maxlen=20)` — lost on restart, only ~100s of data
- `metrics.py` has `calculate_trend()` (linear regression) and `calculate_volatility()` (std of returns) — no RSI, no moving averages, no volume
- AI prompt is buy-the-dip only; no real trading indicators

### Planned: persistent history + trading indicators (Phase 5.3+)

Persisting price history to DB (table `price_history`) unlocks real technical analysis:
- **RSI** — identify oversold conditions (RSI < 30) before executing
- **Moving averages** — MA20/MA50 crossover as trend signal
- **Volume** — validate price moves with volume confirmation

With sufficient history, the strategy `drop_percent` condition becomes a **trigger** (price entered the zone), and the AI decides whether to execute based on RSI + trend + volume. This evolves "buy on X% drop" into genuine algorithmic trading.

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
SOLANA_PRIVATE_KEY=[...]     # unused — ephemeral keys come from user sessions (may be removed)
OPENAI_API_KEY=<key>        # optional
USE_AI=false                # true to enable OpenAI gating
AI_TIMEOUT_SECONDS=5
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=["http://localhost:8080"]
```

> `SOLANA_PRIVATE_KEY` is not used. The ephemeral key architecture (Phase 2) is implemented — execution keys come from per-user sessions, not a server keypair. This variable may be removed.

## Backend Coding Standards

Every new domain (e.g., `alerts`, `positions`) must follow this structure:

```
services/<domain>/
  repository.py     — SQLAlchemy queries only, no business logic
  service.py        — business logic, always returns Pydantic schemas
schemas/<domain>.py — Pydantic v2 input/output shapes
models/<domain>.py  — SQLAlchemy ORM model
api/v1/routers/<domain>.py — HTTP routing
```

### Repository

Extend `SQLAlchemyRepository[Model]` from `app.core.repositories`. Only database queries here.

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.repositories import SQLAlchemyRepository
from app.models.foo import Foo

class FooRepository(SQLAlchemyRepository[Foo]):
    model = Foo

    async def get_by_bar(self, db: AsyncSession, bar_id: int) -> Foo | None:
        stmt = select(self.model).where(self.model.bar_id == bar_id)
        return await self._get_one(db, stmt)
```

**Available base methods** (never reimplement these):
- `get(db, id)` — lookup by PK
- `create(db, entity)` — add + flush
- `update_fields(db, entity, dict)` — setattr + flush
- `delete(db, entity)` — delete + flush
- `list(db, order_by=None)` → `list[Model]`
- `list_paginated(db, params, order_by=None)` → `(list[Model], int)`

### Service

```python
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.pagination import PaginationParams, PaginationMetaBuilder
from app.services.foo.repository import FooRepository
from app.schemas.foo import FooCreate, FooUpdate, FooResponse, FooListItemResponse

class FooService:
    def __init__(self, repository: FooRepository | None = None):
        self.repository = repository or FooRepository()

    async def list(self, db: AsyncSession, params: PaginationParams):
        items, total = await self.repository.list_paginated(db, params)
        meta = PaginationMetaBuilder.build(total, params)
        return [FooListItemResponse.model_validate(i) for i in items], meta

    async def get(self, db: AsyncSession, foo_id: int) -> FooResponse:
        foo = await self.repository.get(db, foo_id)
        if not foo:
            raise HTTPException(status_code=404, detail="Foo not found")
        return FooResponse.model_validate(foo)

    async def create(self, db: AsyncSession, data: FooCreate) -> FooResponse:
        foo = self.repository.model(**data.model_dump())
        await self.repository.create(db, foo)
        return FooResponse.model_validate(foo)

    async def update(self, db: AsyncSession, foo_id: int, data: FooUpdate) -> FooResponse:
        foo = await self.repository.get(db, foo_id)
        if not foo:
            raise HTTPException(status_code=404, detail="Foo not found")
        await self.repository.update_fields(db, foo, data.model_dump(exclude_unset=True))
        return FooResponse.model_validate(foo)

    async def delete(self, db: AsyncSession, foo_id: int) -> None:
        foo = await self.repository.get(db, foo_id)
        if not foo:
            raise HTTPException(status_code=404, detail="Foo not found")
        await self.repository.delete(db, foo)
```

**Service rules:**
- Returns Pydantic schemas (`Schema.model_validate(orm_obj)`), never raw ORM objects
- Raises `HTTPException` for not-found and business errors
- Never calls `db.commit()` — commit belongs in the router
- List methods return `(list[Schema], PageMeta)` tuple

### Schemas

Naming: `FooCreate`, `FooUpdate`, `FooResponse`, `FooListItemResponse`

```python
from datetime import datetime
from pydantic import BaseModel

class FooCreate(BaseModel):
    name: str
    value: float

class FooUpdate(BaseModel):
    name: str | None = None    # all fields optional for PATCH
    value: float | None = None

class FooResponse(BaseModel):
    id: int
    name: str
    value: float
    created_at: datetime
    class Config:
        from_attributes = True

class FooListItemResponse(BaseModel):
    id: int
    name: str                  # omit heavy/unused fields in list view
    class Config:
        from_attributes = True
```

### Router

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_current_user
from app.core.pagination import PaginationParams
from app.core.responses import paginated_response, success_response
from app.db.session import get_db
from app.schemas.foo import FooCreate, FooUpdate
from app.services.foo.service import FooService

router = APIRouter(prefix="/foos", tags=["foos"])

def get_foo_service():
    return FooService()

@router.get("")
async def list_foos(
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    service: FooService = Depends(get_foo_service),
    current_user=Depends(get_current_user),
):
    data, meta = await service.list(db, params)
    return paginated_response([item.model_dump(mode="json") for item in data], meta)

@router.get("/{foo_id}")
async def get_foo(
    foo_id: int,
    db: AsyncSession = Depends(get_db),
    service: FooService = Depends(get_foo_service),
    current_user=Depends(get_current_user),
):
    result = await service.get(db, foo_id)
    return success_response(result.model_dump(mode="json"))

@router.post("", status_code=201)
async def create_foo(
    data: FooCreate,
    db: AsyncSession = Depends(get_db),
    service: FooService = Depends(get_foo_service),
    current_user=Depends(get_current_user),
):
    result = await service.create(db, data)
    await db.commit()
    return success_response(result.model_dump(mode="json"))

@router.patch("/{foo_id}")
async def update_foo(
    foo_id: int,
    data: FooUpdate,
    db: AsyncSession = Depends(get_db),
    service: FooService = Depends(get_foo_service),
    current_user=Depends(get_current_user),
):
    result = await service.update(db, foo_id, data)
    await db.commit()
    return success_response(result.model_dump(mode="json"))

@router.delete("/{foo_id}", status_code=204)
async def delete_foo(
    foo_id: int,
    db: AsyncSession = Depends(get_db),
    service: FooService = Depends(get_foo_service),
    current_user=Depends(get_current_user),
):
    await service.delete(db, foo_id)
    await db.commit()
```

**Router rules:**
- POST → `status_code=201`; DELETE → `status_code=204`, no return value
- Single object response: `success_response(result.model_dump(mode="json"))`
- List response: `paginated_response([item.model_dump(mode="json") for item in data], meta)`
- `db.commit()` in router, never in service
- Service injected via factory: `def get_foo_service(): return FooService()`

### Auth dependency selection

| Use case | Dependency |
|----------|------------|
| Identify the current user | `current_user = Depends(get_current_user)` from `app.core.auth` |
| Resource scoped to a wallet | `wallet = Depends(get_current_wallet)` from `app.core.dependencies` (reads `X-Wallet-Address` header) |

### Register the router

Add to `app/api/v1/router.py`:

```python
from app.api.v1.routers.foo import router as foo_router
router.include_router(foo_router)
```

### Checklist: new domain object

```
[ ] app/models/foo.py              — SQLAlchemy model
[ ] app/models/__init__.py         — add: from .foo import Foo
[ ] alembic revision --autogenerate -m "add foo table"
[ ] alembic upgrade head
[ ] app/services/foo/repository.py
[ ] app/services/foo/service.py
[ ] app/schemas/foo.py
[ ] app/api/v1/routers/foo.py
[ ] app/api/v1/router.py           — router.include_router(foo_router)
```

## Database Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

Migration files: `alembic/versions/`

## Auth

- Phantom wallet signs a message → backend verifies ed25519 signature → issues JWT
- Short-lived access token (60 min) + long-lived refresh token (7 days)
- Both are stateless JWTs with `type` claim (`"access"` / `"refresh"`)
- Frontend auto-refreshes via `POST /api/v1/auth/refresh` on 401

## Key Design Decisions

- **No shared server keypair**: The server holds encrypted ephemeral keys generated per-user client-side, each scoped to a session with `spending_limit` and `expiry`. No master server key exists.
- **Hybrid signing model**: Worker signs autonomously with the user's ephemeral key when an active session exists; falls back to creating `awaiting_signature` / `awaiting_swap` executions for manual Phantom signing when no session is active.
- **Single-worker**: `strategy_runner` is designed for one Uvicorn worker. Multi-worker would need Redis-backed locking.
- **Idempotency**: `external_id` is a deterministic hash of `(strategy_id, price_window)`; unique DB constraint prevents double execution.
- **Price caching**: CoinGecko cached 30s in-process; falls back to last known price on error.
