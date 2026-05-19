# CLAUDE.md — Frontend

React + Vite frontend for SentinelFi. Single-page application where users connect a Phantom wallet, create price-drop strategies, and sign on-chain transactions when the AI agent triggers an execution.

## Stack

- **React 18** + **TypeScript**
- **Vite** (SWC) — dev on port 8080
- **Tailwind CSS v3** + **shadcn/ui** (Radix primitives)
- **React Query (@tanstack/react-query v5)** — server state
- **Axios** — HTTP client with JWT interceptor and auto-refresh
- **React Hook Form** + **Zod** — form validation
- **@solana/web3.js** + **@solana/spl-token** — on-chain interactions
- **Recharts** — price sparklines
- **Vitest** + **@testing-library/react** — unit tests

## Running locally

```bash
npm install
npm run dev        # port 8080
npm run build      # production build
npm run lint       # ESLint
npm run test       # Vitest (once)
npm run test:watch # Vitest (watch)
```

Single file: `npx vitest run src/path/to/file.test.ts`

## Directory Structure

```
src/
  pages/
    Index.tsx        — main page (strategy form, execution list, Phantom modal)
    NotFound.tsx     — 404 page
  components/
    NavLink.tsx      — nav helper
    Sparkline.tsx    — mini price chart
    ui/              — shadcn/ui components (do not edit directly)
  hooks/
    usePhantom.ts    — wallet connect + sendSol/sendUsdc/signAndSendSwap
    useStrategy.ts   — React Query wrapper for strategy CRUD
    useWallet.ts     — React Query wrapper for wallet API
    usePrice.ts      — React Query wrapper for price polling
    useAgent.ts      — React Query wrapper for AI agent status
    useAuth.ts       — JWT auth state
    usePriceSimulator.ts — demo price override
  services/
    api.ts           — Axios instance with JWT interceptor + auto-refresh on 401
    strategy.ts      — getStrategies, createStrategy, toggleStrategy
    auth.ts          — login, refresh
    wallets.ts       — wallet registration
    agent.ts         — agent status
    demo.ts          — override-price for testing
    logs.ts          — execution logs
  assets/
    logo.png         — SentinelFi name logo (transparent, h-[50px] in header)
  test/
    example.test.ts  — Vitest tests
    setup.ts         — jsdom + testing-library setup
public/
  favicon.png        — SentinelFi shield icon
```

## Phantom Wallet Integration (`hooks/usePhantom.ts`)

Three on-chain actions:

| function | use |
|----------|-----|
| `sendSol(toAddress, amountSol)` | SOL transfer (legacy Transaction) |
| `sendUsdc(toAddress, amountUsdc)` | USDC SPL transfer (legacy Transaction) |
| `signAndSendSwap(serializedTxBase64)` | Jupiter swap (VersionedTransaction) |

`signAndSendSwap` deserializes the base64 transaction from the backend and sends it directly via `provider.signAndSendTransaction()` — no re-building needed.

Connection: **devnet** (`clusterApiUrl("devnet")`).

## Strategy Form (Index.tsx)

Two modes toggled by `strategyMode` state:

### Transfer mode (`type: "transfer"`)
- Fields: drop %, SOL amount, destination address, reference price, cooldown, execution mode, token (SOL/USDC)
- Worker executes a direct SOL or USDC transfer using the agent keypair

### Swap mode (`type: "swap"`)
- Fields: drop %, token in/out (SOL ↔ USDC), amount, slippage bps, reference price
- Worker calls Jupiter API for quote + VersionedTransaction
- User signs the Jupiter TX with Phantom

## Execution Signing Flow (`handleSignPhantom` in Index.tsx)

```
execution received
  ├─ has serialized_tx → signAndSendSwap()       # real Jupiter mainnet
  ├─ explanation starts with "Swap" && !serialized_tx → confirm mock swap  # devnet demo
  └─ else → sendSol() or sendUsdc()              # SOL/USDC transfer
```

After signing, calls `PATCH /executions/:id` with `{ tx_hash, status: "completed" }`.

## API Layer (`services/api.ts`)

- Base URL from `VITE_API_URL` env var
- Attaches `Authorization: Bearer <token>` to all requests
- On 401: silently calls `POST /auth/refresh`, updates stored token, retries original request once
- Tokens stored in `localStorage` (`access_token`, `refresh_token`)

## Key Components

- `Sparkline` — renders a small Recharts line chart of recent prices
- `shadcn/ui` components — all in `components/ui/`, generated via shadcn CLI, do not manually edit

## Environment Variables

```
VITE_API_URL=http://localhost:8001/api/v1
```

## Tests

Tests live in `src/test/`. Uses jsdom environment, configured in `vitest.config` (via `vite.config.ts`). Add test files as `*.test.ts` or `*.test.tsx`.

```bash
npx vitest run src/test/example.test.ts
```

## Build Notes

- `vite-plugin-node-polyfills` — required for `@solana/web3.js` and `buffer` in the browser
- `resolveDeduplication` for `react` / `react-dom` prevents double-instance issues with Radix
- Production build output: `dist/`
- Docker: served via nginx on port 80 (exposed as 8080 externally via docker-compose)
