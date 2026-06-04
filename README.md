# SentinelFi

Automated trading strategy execution platform for Solana. Users connect a Phantom wallet, define price-drop strategies, and an AI agent monitors the market and executes trades autonomously via Session Keys.

---

## Vision

SentinelFi is an **Agentic Wallet** — the user defines intentions ("if SOL drops 5%, buy $50 USDC worth"), authorizes the agent once via a Session Key, and the AI executes autonomously within those limits — no Phantom signature needed on each trade.

---

## Architecture

```
Frontend (React/Vite, port 8080)
  └─ Phantom Wallet → Session Key creation + strategy management
Backend (FastAPI, port 8001)
  ├─ Strategy Worker — polls CoinGecko every 5s, evaluates AI, executes
  ├─ Sessions Service — stores encrypted ephemeral keys per user
  └─ AI Agent (OpenAI, optional) — gates execution decisions
PostgreSQL 17
Solana
  └─ Anchor Program — SessionToken accounts (Phase 2 ✅)
```

---

## Session Keys Architecture

The core differentiator. Each user generates an ephemeral keypair in the browser and signs once via Phantom to create an on-chain `SessionToken`:

```
SessionToken {
  owner:          user's Phantom wallet
  delegate:       ephemeral_pubkey       ← generated in browser
  spending_limit: e.g. 50 USDC
  expiry:         e.g. 7 days from now
}
```

The backend stores the encrypted ephemeral private key per user. When a strategy triggers, the worker signs autonomously using that key — no Phantom interaction needed. The user can revoke at any time.

There is **no shared server keypair**. Each session is user-specific, scoped, and expiring.

---

## Core Concepts

### Strategy
Defines the execution rule:
- Price drop threshold (%)
- Amount to invest
- Token pair (SOL/USDC)
- Cooldown period
- Execution mode (once / recurring)

### Execution
Record of each triggered action:
- Status: `awaiting_signature` → `completed` / `expired` / `skipped`
- tx_hash (on-chain confirmation)
- AI explanation
- Full audit trail

### Session
User-delegated authority for the AI agent:
- On-chain `SessionToken` (Anchor program)
- Spending limit enforced on-chain
- Auto-expires; user can revoke

---

## Stack

### Backend
- FastAPI + SQLAlchemy 2 + PostgreSQL
- Pydantic v2
- solders + solana-py
- httpx (CoinGecko, Jupiter API v6)
- OpenAI SDK (optional)

### Frontend
- React 18 + TypeScript
- Vite (SWC) + Tailwind CSS + shadcn/ui
- React Query + Axios
- @solana/web3.js + @solana/spl-token

### Blockchain
- Solana (devnet → mainnet)
- Anchor/Rust (Session Keys program — Phase 2 ✅)
- Jupiter API v6 (swaps)

---

## Auth

- Phantom wallet signs a challenge (ed25519) → backend issues JWT
- Access token (60 min) + refresh token (7 days)
- Silent renewal via `POST /api/v1/auth/refresh` on 401

---

## Roadmap

### Phase 1 — Foundation ✅ **COMPLETE**
- [x] FastAPI + SQLAlchemy 2 + PostgreSQL 17
- [x] Phantom wallet authentication (ed25519 challenge + JWT)
- [x] Strategy CRUD (create, list, update, delete)
- [x] Execution tracking with status pipeline
- [x] Worker loop (polls CoinGecko every 5s)
- [x] Frontend (React 18 + TypeScript + Vite)
- [x] Docker stack (backend, frontend, postgres)

### Phase 2 — Anchor + Session Keys ✅ **COMPLETE**
- [x] Anchor program: `create_session` instruction
- [x] Anchor program: `execute_swap` instruction
- [x] Anchor program: `revoke_session` instruction
- [x] SessionToken PDA with `owner`, `delegate`, `spending_limit`, `expiry`, `amount_spent`, `bump`
- [x] Devnet deployment (Program ID: `HwPkZA1WSussRBD8hgRojJ2bg2Upxa1wr428gBzzoATB`)
- [x] Backend: Store encrypted ephemeral keys per user (Fernet encryption)
- [x] Backend: Session management endpoints (`POST /sessions`, `GET /sessions`, `DELETE /sessions`)
- [x] Backend: Worker autonomous execution (signs with ephemeral keypair when session active)
- [x] Frontend: "Authorize Agent" flow (generate keypair → sign once → store encrypted key)
- [x] Frontend: Session status UI (active, delegate, spending limit, expiry)
- [x] Jupiter API v6 integration (quote + swap TX construction)
- [x] Jupiter mock fallback (for devnet testing)
- [x] AI Agent pipeline (base filter → trend → volatility → OpenAI → heuristic fallback)
- [x] Execution status pipeline (`awaiting_signature` → `completed`/`expired`/`skipped`)
- [x] Idempotency via `external_id` (prevents duplicate execution in same price window)
- [x] Demo endpoint: `POST /demo/set-price` for manual testing

### Phase 3 — Jupiter Mainnet ⏳ **NOT STARTED**
- [ ] Mainnet RPC endpoint configuration
- [ ] VersionedTransaction validation on mainnet
- [ ] Remove `[DEMO]` suffix via environment variable
- [ ] Add token pairs: BONK, JTO, PYTH, WIF

### Phase 3.5 — x402 (Autonomous Agent Payments) ⏳ **NOT STARTED**

The [x402 protocol](https://x402.org) standardizes HTTP `402 Payment Required` for machine-to-machine USDC payments. The agent pays autonomously using the session's ephemeral key — no human intervention needed.

- [ ] Agent pays for premium price data (Pyth) per query via x402
- [ ] AI inference cost debited from user session via x402 (not server's OpenAI bill)
- [ ] Monetize SentinelFi API — external agents pay per strategy execution
- [ ] Replace CoinGecko with Pyth Network feeds

> Requires Phase 2 (Session Keys) + Phase 3 (mainnet). The `spending_limit` of a session covers both swaps and x402 data costs — user authorizes a total budget and the agent allocates it.

### Phase 4 — Multi-user at Scale ⏳ **NOT STARTED**
- [ ] Worker validates on-chain session before each execution
- [ ] Session expiry management and renewal UX
- [ ] Redis-backed locking for multi-worker Uvicorn

### Phase 5 — Product & Intelligence ⏳ **NOT STARTED**
- [ ] Pix on-ramp — user deposits BRL via Pix, receives USDC on-chain (via gateway: Stripe/MoonPay/Transak)
- [ ] Persistent price history — table `price_history` in DB; worker persists every tick; replaces in-memory deque (currently maxlen=20, lost on restart)
- [ ] Trading indicators — RSI, MA20/MA50, volume in `metrics.py`; strategy `drop_percent` becomes entry trigger, AI decides based on indicators
- [ ] P&L dashboard per strategy
- [ ] Email / webhook notifications on execution
- [ ] Stop-loss, take-profit, DCA strategy types

---

## Running locally

```bash
# Backend
cd backend && pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8001

# Frontend
cd frontend && npm install
npm run dev

# Docker
docker network create app_network
docker-compose up --build
```

See `backend/CLAUDE.md` and `frontend/CLAUDE.md` for detailed development guides.
