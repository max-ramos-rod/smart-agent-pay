# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

SentinelFi is an automated trading strategy execution platform for Solana. Users connect a Phantom wallet, define price-drop strategies, and a background worker monitors CoinGecko prices every 5 seconds. When a strategy triggers, the worker executes autonomously within the user's Session Key limits — or, if no session is active, creates a pending execution for the user to sign via Phantom.

Target: **Solana Frontier Hackathon 2026**. Core differentiator: Session Keys architecture where users delegate spending authority once, and the AI agent acts fully autonomously within those limits.

## Development Commands

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
pip install -r requirements.txt
alembic upgrade head
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

Single test file: `npx vitest run src/path/to/file.test.ts`

### Docker (full stack)

```bash
docker-compose up --build
```

Requires an external Docker network:
```bash
docker network create app_network
```

## Architecture

```
Frontend (React/TS, port 8080)
  └─ Axios + React Query → REST API
Backend (FastAPI, port 8001)
  ├─ Routers → Services → Repositories → PostgreSQL
  ├─ Background Worker (strategy_runner) — polls CoinGecko every 5s
  └─ AI Agent (optional, OpenAI) — gates execution decisions
PostgreSQL 17
Solana (devnet → mainnet)
  └─ Anchor Program — SessionToken accounts per user (deployed devnet)
```

## Session Keys Architecture (implemented — core differentiator)

The goal is **fully autonomous execution** without the user signing each transaction.

### Flow

```
1. User clicks "Authorize Agent" in frontend
2. Browser generates an ephemeral keypair (via @solana/web3.js)
3. User signs once via Phantom, creating on-chain:
     SessionToken {
       owner:          user's Phantom wallet,
       delegate:       ephemeral_pubkey,      ← generated in browser
       spending_limit: user-defined (e.g. 50 USDC),
       expiry:         user-defined (e.g. 7 days)
     }
4. ephemeral_private_key is sent to the backend and stored encrypted per user
5. Worker checks active session → signs autonomously with that user's ephemeral key
6. User can revoke at any time via revoke_session instruction
```

### Why ephemeral keys per user (not one server keypair)

- Server never holds a master key — only scoped, expiring, user-specific keys
- If server is compromised, attacker gets keys limited by `spending_limit` + `expiry`
- Each session is an auditable on-chain account
- Users control scope and revocation

### DB schema for sessions

```
sessions
  user_id
  delegate_pubkey           ← on-chain delegate
  encrypted_private_key     ← ephemeral key, AES-encrypted, stored per user
  spending_limit            ← max amount the agent can spend
  expiry                    ← UTC datetime
  session_token_address     ← on-chain SessionToken PDA
```

## Execution Flow

**With active session (autonomous):** Worker detects price drop → checks active session → signs with ephemeral key → creates `completed` execution directly.

**Without session (manual fallback):** Worker detects price drop → creates `awaiting_signature` or `awaiting_swap` execution in DB → frontend polls → user clicks to sign via Phantom → frontend PATCHes execution with `tx_hash`.

## Backend Layer Pattern

All routes follow: **Router → Service → Repository → DB**

- `app/routers/` — HTTP routing, request/response shapes
- `app/services/` — business logic, orchestration
- `app/repositories/` — SQLAlchemy queries (async)
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic v2 schemas

All API responses use an envelope: `{ "data": {...}, "meta": { ...pagination } }`

## Key Backend Files

| Path | Purpose |
|------|---------|
| `app/workers/strategy_runner.py` | Core loop: polls price, evaluates AI, creates pending executions |
| `app/services/solana/service.py` | SOL/USDC transfer construction (uses ephemeral keypair from session) |
| `app/services/jupiter/service.py` | Jupiter API v6 — quote, swap TX, mock fallback |
| `app/services/ai/agent.py` | OpenAI-based execution gating (enabled via `USE_AI=true`) |
| `app/services/execution/service.py` | Execution CRUD, expiry logic |
| `app/api/v1/routers/sessions.py` | Session key management — POST/GET/DELETE (implemented) |
| `app/api/v1/routers/demo.py` | `POST /demo/override-price` — inject fake price for testing |
| `backend/scripts/gera_token.py` | Generate JWT tokens for manual testing |

## Frontend Structure

- `src/services/` — Axios API call wrappers (one file per domain)
- `src/hooks/` — React Query hooks (`useStrategy`, `useWallet`, `usePrice`, `useAgent`, `usePhantom`, `useSession`)
- `src/pages/` — Route-level page components
- `src/components/` — Reusable UI components (shadcn/ui + Radix primitives)
- `src/test/` — Vitest tests, jsdom environment

## Environment Variables

**Backend** (`backend/.env`):
```
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
SECRET_KEY=<jwt-signing-key>
SOLANA_PRIVATE_KEY=[...]          # unused — ephemeral keys come from user sessions (may be removed)
OPENAI_API_KEY=<key>             # optional
USE_AI=false
AI_TIMEOUT_SECONDS=5
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=["http://localhost:8080"]
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

Migration files: `backend/alembic/versions/`.

## WSL / Linux Setup

The Anchor/Solana smart contract work runs in WSL. The main SentinelFi app can also run there.

### First-time clone in WSL

```bash
git clone https://github.com/max-ramos-rod/smart-agent-pay.git sentinelfi
cd sentinelfi
```

### Recreate .env files (not in git — copy from Windows or recreate manually)

```
backend/.env        — DATABASE_URL, SECRET_KEY, SOLANA_PRIVATE_KEY, OPENAI_API_KEY, USE_AI
backend/.env.db     — POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
frontend/.env       — VITE_API_URL=http://localhost:8001/api/v1
```

### Option A — Docker (recommended, no local installs needed)

```bash
docker network create app_network   # only once
docker-compose up --build
```

PostgreSQL, backend, and frontend all run in containers. No Python venv or npm install required.

### Option B — Native (faster hot reload during development)

Requires Python 3.11+ and Node 18+ installed on the host.

```bash
# backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8001

# frontend (separate terminal)
cd frontend
npm install
npm run dev
```

When running natively, still use Docker for the database:
```bash
docker-compose up db
```

### Docker (full stack in WSL)

```bash
docker network create app_network   # only once
docker-compose up --build
```

### Solana / Anchor environment (already set up in WSL)

The Solana CLI and Anchor toolchain are already installed in WSL from a separate project. Reuse that environment for any smart contract work on top of SentinelFi.

