# SentinelFi

Automated trading strategy execution platform for Solana. Users connect a Phantom wallet, define price-drop strategies, and an AI agent monitors the market. The current implementation supports manual Phantom signing, Session Key creation/revocation, and autonomous transfer attempts with the user's encrypted ephemeral key.

---

## Vision

SentinelFi is moving toward an **Agentic Wallet** — the user defines intentions ("if SOL drops 5%, buy $50 USDC worth"), authorizes the agent once via a Session Key, and the agent executes within scoped limits. Today, the Session Key account exists on-chain and the backend can use the ephemeral key for autonomous transfers, but on-chain spending-limit validation still needs to be wired into every autonomous execution path.

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
  └─ Anchor Program — SessionToken accounts (devnet, partially integrated)
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

The backend stores the encrypted ephemeral private key per user. When a transfer strategy triggers and a DB session is active, the worker attempts to sign using that key. The user can revoke the on-chain SessionToken and the backend session.

There is **no shared server keypair**. Each session is user-specific, scoped, and expiring.

Current integration boundary:
- `create_session` and `revoke_session` are called from the frontend on devnet.
- `execute_swap` exists in the Anchor program and validates `expiry` + `spending_limit`, but the backend does not yet call it before autonomous transfers/swaps.
- Jupiter swaps currently produce a transaction for Phantom/manual signing; autonomous swap signing is not complete.

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
- Status: `awaiting_signature` → `success` / `failed` / `expired`
- tx_hash (on-chain confirmation)
- AI explanation
- Full audit trail

### Session
User-delegated authority for the AI agent:
- On-chain `SessionToken` (Anchor program)
- Spending limit represented on-chain; enforcement exists in `execute_swap`, but worker integration is pending
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

### Phase 2 — Anchor + Session Keys 🔄 **PARTIALLY COMPLETE**
- [x] Anchor program: `create_session` instruction
- [x] Anchor program: `execute_swap` instruction
- [x] Anchor program: `revoke_session` instruction
- [x] SessionToken PDA with `owner`, `delegate`, `spending_limit`, `expiry`, `amount_spent`, `bump`
- [x] Devnet deployment (Program ID: `HwPkZA1WSussRBD8hgRojJ2bg2Upxa1wr428gBzzoATB`)
- [x] Backend: Store encrypted ephemeral keys per user (Fernet encryption)
- [x] Backend: Session management endpoints (`POST /sessions`, `GET /sessions`, `DELETE /sessions`)
- [x] Backend: Worker autonomous transfer attempt (signs with ephemeral keypair when session active)
- [x] Frontend: "Authorize Agent" flow (generate keypair → sign once → store encrypted key)
- [x] Frontend: Session status UI (active, delegate, spending limit, expiry)
- [x] Jupiter API v6 integration (quote + swap TX construction)
- [x] Jupiter mock fallback (for devnet testing)
- [x] AI Agent pipeline (base filter → trend → volatility → OpenAI → heuristic fallback)
- [x] Execution status pipeline (`awaiting_signature` → `success`/`failed`/`expired`)
- [x] Idempotency via `external_id` (prevents duplicate execution in same price window)
- [x] Demo endpoint: `POST /demo/set-price` for manual testing
- [ ] Backend calls Anchor `execute_swap` / session-limit accounting before autonomous execution
- [ ] Autonomous Jupiter swap signing with the ephemeral delegate key
- [ ] Validate on-chain SessionToken before each autonomous execution

### Phase 3 — Jupiter Mainnet 🔄 **IN PROGRESS**
- [x] Mainnet RPC endpoint configuration (`SOLANA_RPC_URL` env var)
- [x] Dual-environment support (`npm run dev:devnet` / `npm run dev:mainnet`)
- [x] USDC mint address configurable per environment
- [ ] VersionedTransaction validation on mainnet (end-to-end test pending)
- [ ] Align Session Key network with swap/transfer network (devnet vs mainnet)
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

### Phase 4.5 — Observability ⏳ **PARTIALLY DONE**
- [x] Loguru — structured logging to file (`logs/sentinelfi.log`, `logs/errors.log`)
- [x] ErrorBoundary — frontend crash capture
- [x] Sentry opt-in (`VITE_SENTRY_DSN` env var — disabled by default)
- [ ] Loki — log aggregation (add when traffic justifies)
- [ ] Grafana — dashboards for logs + metrics (add with Loki)
- [ ] Prometheus + `prometheus-fastapi-instrumentator` — metrics (req/s, latency, worker health)

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
