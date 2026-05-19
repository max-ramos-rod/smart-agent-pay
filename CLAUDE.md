<<<<<<< Updated upstream
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SentinelFi is an automated trading strategy execution platform for Solana. Users connect a Phantom wallet, define price-drop strategies, and a background worker monitors CoinGecko prices every 5 seconds to execute on-chain transfers or Jupiter swaps automatically. An optional AI layer (OpenAI gpt-4o-mini) gates execution decisions using a "buy the dip" heuristic.

## Development Commands

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
alembic upgrade head             # run DB migrations
uvicorn app.main:app --reload --port 8001
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev          # dev server on port 8080
npm run build        # production build
npm run lint         # ESLint
npm run test         # run tests once (Vitest)
npm run test:watch   # watch mode
```

To run a single test file:
```bash
cd frontend
npx vitest run src/path/to/file.test.ts
```

### Docker (full stack)

```bash
docker-compose up --build
```

Requires an external Docker network named `app_network`:
```bash
docker network create app_network
```

## Architecture

```
Frontend (React/TS, port 8080)
  └─ Axios + React Query → REST API
Backend (FastAPI, port 8001)
  ├─ Routers → Services → Repositories → PostgreSQL
  ├─ Background Worker (strategy_runner) — runs on startup
  │     polls CoinGecko every 5s, evaluates AI decision, creates execution
  └─ AI Agent (optional, OpenAI gpt-4o-mini) — gates execution decisions
PostgreSQL 17
```

### Backend Layer Pattern

All routes follow: **Router → Service → Repository → DB**

- `app/routers/` — HTTP routing, request/response shapes
- `app/services/` — business logic, orchestration
- `app/repositories/` — SQLAlchemy queries (async)
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic v2 schemas

All API responses use an envelope:
```json
{ "data": {...}, "meta": { ...pagination } }
```

### Key Backend Services

| Path | Purpose |
|------|---------|
| `app/workers/strategy_runner.py` | Core background task; polls price every 5s, evaluates AI, bifurcates on strategy type (transfer vs swap), deduplicates via `external_id` |
| `app/services/solana/service.py` | Solana SDK interactions, wallet signing, SOL transfers |
| `app/services/jupiter/service.py` | Jupiter API v6 integration — quote, swap TX, mock fallback for devnet |
| `app/services/ai/agent.py` | OpenAI-based execution gating (enabled via `USE_AI=true`); falls back to heuristic on timeout |
| `app/services/ai/metrics.py` | `calculate_trend()` and `calculate_volatility()` for local price analysis |
| `app/services/strategy/` | Strategy CRUD and evaluation logic |
| `app/services/execution/service.py` | Execution logging, `create_awaiting_signature()`, `create_awaiting_swap()`, expiry |
| `backend/scripts/gera_token.py` | Generate JWT tokens for manual testing |
| `backend/scripts/reset_executions.py` | Reset execution records in DB |

### Frontend Structure

- `src/services/` — Axios API call wrappers (one file per domain)
- `src/hooks/` — React Query hooks wrapping services (`useStrategy`, `useWallet`, `usePrice`, `useAgent`, `usePhantom`)
- `src/hooks/usePhantom.ts` — wallet connection + `signAndSendSwap()` for Jupiter VersionedTransactions
- `src/pages/Index.tsx` — main page; handles transfer/swap form, execution modal, Phantom signing flow
- `src/components/` — Reusable UI components (shadcn/ui + Radix primitives)
- `src/assets/logo.png` — SentinelFi logo (text only, transparent background)
- `public/favicon.png` — SentinelFi shield favicon
- `src/test/` — Vitest tests, jsdom environment

## Environment Variables

**Backend** (`backend/.env` — copy from `backend/.env.example`):
```
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
SECRET_KEY=<jwt-signing-key>
SOLANA_PRIVATE_KEY=[...]                      # JSON array format (agent keypair)
OPENAI_API_KEY=<key>                          # optional, enables AI gating
USE_AI=false                                  # set true to enable OpenAI gating
AI_TIMEOUT_SECONDS=5
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=["http://localhost:8080"]     # optional, default covers localhost dev
```

**Frontend** (`frontend/.env`):
```
VITE_API_URL=http://localhost:8001/api/v1
```

## Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

Migration files live in `backend/alembic/versions/`.

## Strategy Types

Strategies have a `type` field that drives worker bifurcation:

| type | behaviour |
|------|-----------|
| `transfer` | Worker creates `awaiting_signature` execution; user signs SOL transfer with Phantom |
| `swap` | Worker calls Jupiter API for quote + swap TX; creates `awaiting_swap` execution; user signs VersionedTransaction with Phantom |

### Strategy Fields (relevant subset)

```python
type: str                 # "transfer" | "swap"
token: str                # "SOL" | "USDC" (used for transfer)
amount_sol: float         # SOL amount (for transfer, or swap input when token_in="SOL")
amount_usdc: float | None # USDC amount (for swap input when token_in="USDC")
token_in: str | None      # "SOL" | "USDC"  (swap only)
token_out: str | None     # "SOL" | "USDC"  (swap only)
slippage_bps: int | None  # basis points, e.g. 50 = 0.5% (swap only)
drop_percent: float       # trigger threshold
reference_price: float    # price at strategy creation
execution_mode: str       # "once" | "recurring"
cooldown_seconds: int     # min seconds between executions
```

## Execution Statuses

| status | meaning |
|--------|---------|
| `awaiting_signature` | transfer pending user Phantom signature |
| `awaiting_swap` | Jupiter swap pending user Phantom signature |
| `completed` | TX confirmed on-chain |
| `expired` | pending for >3 minutes, auto-expired by worker |
| `skipped` | AI or heuristic decided not to execute |

The `Execution` model also has:
- `serialized_tx: Text | None` — base64 Jupiter VersionedTransaction (null for transfers and mock swaps)
- `external_id: str | None` — deterministic idempotency key; unique DB constraint prevents duplicate executions

## Jupiter Swap Integration

Jupiter API v6 operates on **mainnet only**. In devnet environments the worker gracefully degrades:

1. `get_quote_safe()` catches any API failure and returns `None`
2. If None (or `_mock: True`), `mock_quote()` generates a realistic fake quote (~$150/SOL)
3. `serialized_tx` is `None` for mock swaps
4. Frontend detects mock: `explanation?.startsWith("Swap") && !serialized_tx` → confirms without real Phantom interaction
5. Real mainnet swaps: `serialized_tx` is base64 VersionedTransaction; `signAndSendSwap()` in `usePhantom.ts` deserializes and sends it

**Token mints (mainnet):**
```python
TOKEN_MINTS = {
    "SOL":  "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
}
```

## AI Agent

Located at `app/services/ai/agent.py`. Evaluation pipeline:

1. **Base filter** — if drop < 50% of target, skip without calling AI (cost guard)
2. **Local heuristics** — if trend < -0.5 (sharp fall) or volatility > 0.15, reject
3. **OpenAI call** (only if `USE_AI=true` and history ≥ 5 points) — gpt-4o-mini with "buy the dip" context prompt
4. **Fallback heuristic** — if OpenAI times out or errors, use simple drop-threshold comparison

The prompt explains the "buy the dip" intent explicitly and instructs the model to **approve** unless there is continuous freefall or extreme volatility.

## Key Design Decisions

- **Single-worker constraint**: `strategy_runner` is designed for one Uvicorn worker. Scaling to multiple workers requires a Redis-backed lock/queue.
- **Idempotency**: Executions are deduplicated via `external_id` (unique DB constraint); the worker generates a deterministic ID before submitting.
- **Price caching**: CoinGecko responses are cached 30 seconds inside the worker to avoid rate-limiting. Falls back to last known price on error.
- **Demo mode**: `POST /api/v1/demo/override-price` accepts a fake price for testing strategy triggers without real market movement.
- **AI gating**: When `USE_AI=true`, the AI agent must approve each execution; times out after `AI_TIMEOUT_SECONDS` and falls back to heuristic.
- **Refresh token**: Auth issues a short-lived access token (60 min) + long-lived refresh token (7 days). Both are stateless JWTs differentiated by `type` claim (`"access"` / `"refresh"`). The frontend interceptor renews silently via `POST /api/v1/auth/refresh` on 401.
- **CORS**: Allowed origins driven by `ALLOWED_ORIGINS` env var. Defaults to `["http://localhost:8080", "http://localhost:5173"]` for local dev.
- **Agent keypair**: A single server-side Solana keypair signs SOL transfers. For Jupiter swaps the user's Phantom wallet signs the VersionedTransaction directly — the agent keypair is not used.
=======
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SentinelFi is an automated trading strategy execution platform for Solana. Users connect a Phantom wallet, define price-drop strategies, and a background worker monitors CoinGecko prices every 5 seconds to execute on-chain transfers automatically. An optional AI layer (OpenAI) can make execution decisions.

## Development Commands

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
alembic upgrade head             # run DB migrations
uvicorn app.main:app --reload --port 8001
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev          # dev server on port 8080
npm run build        # production build
npm run lint         # ESLint
npm run test         # run tests once (Vitest)
npm run test:watch   # watch mode
```

To run a single test file:
```bash
cd frontend
npx vitest run src/path/to/file.test.ts
```

### Docker (full stack)

```bash
docker-compose up --build
```

Requires an external Docker network named `app_network`:
```bash
docker network create app_network
```

## Architecture

```
Frontend (React/TS, port 8080)
  └─ Axios + React Query → REST API
Backend (FastAPI, port 8001)
  ├─ Routers → Services → Repositories → PostgreSQL
  ├─ Background Worker (strategy_runner) — runs on startup
  │     polls CoinGecko every 5s, executes Solana transfers
  └─ AI Agent (optional, OpenAI) — gates execution decisions
PostgreSQL 17
```

### Backend Layer Pattern

All routes follow: **Router → Service → Repository → DB**

- `app/routers/` — HTTP routing, request/response shapes
- `app/services/` — business logic, orchestration
- `app/repositories/` — SQLAlchemy queries (async)
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic v2 schemas

All API responses use an envelope:
```json
{ "data": {...}, "meta": { ...pagination } }
```

### Key Backend Services

| Path | Purpose |
|------|---------|
| `app/workers/strategy_runner.py` | Core background task; polls price, evaluates strategies, submits Solana TXs, deduplicates via `external_id` |
| `app/services/solana/` | Solana SDK interactions, wallet signing, transfers |
| `app/services/ai/agent.py` | OpenAI-based execution gating (enabled via `USE_AI=true`) |
| `app/services/strategy/` | Strategy CRUD and evaluation logic |
| `app/services/execution/` | Execution logging and audit trail |
| `backend/scripts/gera_token.py` | Generate JWT tokens for manual testing |
| `backend/scripts/reset_executions.py` | Reset execution records in DB |

### Frontend Structure

- `src/services/` — Axios API call wrappers (one file per domain)
- `src/hooks/` — React Query hooks wrapping services (`useStrategy`, `useWallet`, `usePrice`, `useAgent`, `usePhantom`)
- `src/pages/` — Route-level page components
- `src/components/` — Reusable UI components (shadcn/ui + Radix primitives)
- `src/test/` — Vitest tests, jsdom environment

## Environment Variables

**Backend** (`backend/.env` — copiar de `backend/.env.example`):
```
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
SECRET_KEY=<jwt-signing-key>
SOLANA_PRIVATE_KEY=[...]                      # JSON array format
OPENAI_API_KEY=<key>                          # optional
USE_AI=false
AI_TIMEOUT_SECONDS=5
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=["http://localhost:8080"]     # optional, default cobre localhost dev
```

**Frontend** (`frontend/.env`):
```
VITE_API_URL=http://localhost:8001/api/v1
```

## Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

Migration files live in `backend/alembic/versions/`.

## Key Design Decisions

- **Single-worker constraint**: `strategy_runner` is designed for one Uvicorn worker. Scaling to multiple workers requires a Redis-backed lock/queue (noted in code comments).
- **Idempotency**: Executions are deduplicated via `external_id` (unique DB constraint); the worker generates a deterministic ID before submitting to Solana.
- **Price caching**: CoinGecko responses are cached 30 seconds inside the worker to avoid rate-limiting.
- **Demo mode**: `POST /api/v1/demo/override-price` accepts a fake price for testing strategy triggers without real market movement.
- **AI gating**: When `USE_AI=true`, the AI agent must approve each execution; it times out after `AI_TIMEOUT_SECONDS` and falls back to rule-based execution.
- **Refresh token**: Auth issues a short-lived access token (60 min) + long-lived refresh token (7 days). Both are stateless JWTs differentiated by `type` claim (`"access"` / `"refresh"`). The frontend interceptor renews silently via `POST /api/v1/auth/refresh` on 401, without requiring a new Phantom wallet signature.
- **CORS**: Allowed origins are driven by `ALLOWED_ORIGINS` env var (list of strings). Defaults to `["http://localhost:8080", "http://localhost:5173"]` for local dev.
>>>>>>> Stashed changes
