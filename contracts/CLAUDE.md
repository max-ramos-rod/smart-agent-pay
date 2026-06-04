# CLAUDE.md — Contracts (Anchor / Rust)

Anchor program on Solana that implements the Session Keys architecture for SentinelFi. Users delegate spending authority once (on-chain `SessionToken`); the backend agent operates autonomously within those limits.

**Program ID (devnet):** `HwPkZA1WSussRBD8hgRojJ2bg2Upxa1wr428gBzzoATB`

Current integration note: `create_session` and `revoke_session` are called by the frontend. `execute_swap` enforces `expiry` and `spending_limit` in the program, but the backend worker does not yet call it before autonomous transfer/swap execution, so on-chain spending-limit accounting is still pending integration.

## Toolchain

| Tool | Version |
|------|---------|
| Rust | 1.95.0 (via `rust-toolchain.toml`) |
| Solana CLI (Agave) | 3.1.15 |
| Anchor CLI | 1.0.2 |
| AVM | 1.0.0 |
| Node (JS tests) | via Yarn |

> The npm package for Anchor 1.0 is **`@anchor-lang/core`** — not `@coral-xyz/anchor`. Use this in all TS files.

## Development Commands

```bash
cd contracts

# Build program
anchor build

# Deploy to devnet (requires funded wallet at ~/.config/solana/id.json)
anchor deploy

# Run Rust tests
cargo test --manifest-path programs/sentinelfi/Cargo.toml

# Run TS tests (after anchor build)
anchor test --skip-local-validator
```

After `anchor build`, copy the updated IDL to the frontend:

```bash
cp target/idl/sentinelfi.json ../frontend/src/idl/sentinelfi.json
```

## Program Structure

```
programs/sentinelfi/src/
  lib.rs            — program entry point, declares instructions
  state.rs          — on-chain account structs
  error.rs          — custom error codes
  constants.rs      — PDA seeds and global constants
  instructions.rs   — re-exports all instruction modules
  instructions/
    create_session.rs
    execute_swap.rs
    revoke_session.rs
```

## Anchor Patterns

### lib.rs — program entry point

`lib.rs` declares the program ID and lists every public instruction. Each instruction delegates to its module's `handler` function:

```rust
use anchor_lang::prelude::*;
pub use instructions::*;

declare_id!("HwPkZA1WSussRBD8hgRojJ2bg2Upxa1wr428gBzzoATB");

#[program]
pub mod sentinelfi {
    use super::*;

    pub fn my_instruction(ctx: Context<MyInstruction>, param: u64) -> Result<()> {
        instructions::my_instruction::handler(ctx, param)
    }
}
```

### instructions.rs — module re-exports

Re-export every instruction module so `lib.rs` can use `instructions::<module>::handler`:

```rust
#[allow(ambiguous_glob_reexports)]   // required — all handlers are named "handler"
pub mod create_session;
pub mod execute_swap;
pub mod my_new_instruction;
pub use create_session::*;
pub use execute_swap::*;
pub use my_new_instruction::*;
```

> `#[allow(ambiguous_glob_reexports)]` is required because every module exports a `handler` function with the same name.

### Instruction file pattern

Each instruction lives in `instructions/<name>.rs` and follows this shape:

```rust
use anchor_lang::prelude::*;
use crate::state::SessionToken;
use crate::error::ErrorCode;
use crate::constants::SESSION_SEED;

// 1. Accounts struct — declares required accounts and constraints
#[derive(Accounts)]
pub struct MyInstruction<'info> {
    #[account(mut)]
    pub signer: Signer<'info>,

    #[account(
        mut,
        seeds = [SESSION_SEED, signer.key().as_ref()],
        bump = session_token.bump,
        has_one = signer @ ErrorCode::Unauthorized,
    )]
    pub session_token: Account<'info, SessionToken>,
}

// 2. Handler — business logic
pub fn handler(ctx: Context<MyInstruction>, amount: u64) -> Result<()> {
    let session = &mut ctx.accounts.session_token;
    require!(condition, ErrorCode::SomeError);
    session.field = value;
    Ok(())
}
```

**Account constraint reference:**

| Constraint | Effect |
|------------|--------|
| `init` | Creates account; needs `payer`, `space`, `system_program` |
| `mut` | Marks account writable |
| `seeds = [...]` | Derives PDA — must match derivation in client |
| `bump = account.bump` | Validates stored bump (more efficient than re-deriving) |
| `has_one = field @ Err` | Checks `account.field == accounts.field.key()`, returns `Err` if not |
| `close = target` | Zeroes account and transfers lamports to `target` on instruction end |

**UncheckedAccount:** When Anchor cannot verify an account (e.g., an ephemeral pubkey that may not exist on-chain), use `UncheckedAccount` with a mandatory `/// CHECK:` doc comment explaining why it is safe:

```rust
/// CHECK: delegate is the ephemeral pubkey from the browser — it may not be an on-chain account
pub delegate: UncheckedAccount<'info>,
```

### state.rs — on-chain account structs

```rust
use anchor_lang::prelude::*;

#[account]
pub struct MyAccount {
    pub owner: Pubkey,
    pub value: u64,
    pub bump: u8,      // always store the PDA bump
}

impl MyAccount {
    pub const LEN: usize = 8   // discriminator (mandatory for #[account])
        + 32  // owner: Pubkey
        + 8   // value: u64
        + 1;  // bump: u8
}
```

**Type sizes for `LEN`:**

| Type | Bytes |
|------|-------|
| discriminator | 8 (always first) |
| `Pubkey` | 32 |
| `u64` / `i64` | 8 |
| `u32` / `i32` | 4 |
| `u8` / `bool` | 1 |
| `String` (len n) | 4 + n |
| `Vec<T>` (len n) | 4 + n × size(T) |

### error.rs — custom errors

```rust
use anchor_lang::prelude::*;

#[error_code]
pub enum ErrorCode {
    #[msg("Session has expired")]
    SessionExpired,          // 6000
    #[msg("Spending limit exceeded")]
    SpendingLimitExceeded,   // 6001
    #[msg("Not authorized: caller is not the delegate")]
    Unauthorized,            // 6002
    #[msg("Not authorized: caller is not the session owner")]
    NotOwner,                // 6003
}
```

Codes start at 6000. New errors append to the enum — never reorder existing entries (clients reference codes numerically).

### constants.rs — PDA seeds

```rust
pub const SESSION_SEED: &[u8] = b"session";
// pub const OTHER_SEED: &[u8] = b"other";
```

Seeds must match exactly on the client side (frontend `PublicKey.findProgramAddressSync`).

## On-Chain Architecture

### SessionToken PDA

- **Seeds:** `["session", owner_pubkey]`
- **Payer / rent:** owner (returned on revoke via `close = owner`)
- **One session per user** — the PDA is deterministic from owner pubkey; creating a new one overwrites the old

```
SessionToken {
    owner:          Pubkey,  // Phantom wallet
    delegate:       Pubkey,  // ephemeral pubkey from browser
    spending_limit: u64,     // micro-USDC (50 USDC = 50_000_000)
    amount_spent:   u64,     // accumulated; checked on every execute_swap
    expiry:         i64,     // Unix timestamp UTC
    bump:           u8,
}
```

### Instructions

| Instruction | Signer | Effect |
|-------------|--------|--------|
| `create_session` | owner (Phantom) | Initializes `SessionToken` PDA; sets delegate + limits |
| `execute_swap` | delegate (ephemeral key) | Validates expiry + limit; increments `amount_spent` |
| `revoke_session` | owner (Phantom) | Closes account; returns rent to owner |

## Client Integration

Frontend derives the PDA before calling any instruction:

```ts
import { PublicKey } from "@solana/web3.js";

const [sessionTokenPda] = PublicKey.findProgramAddressSync(
  [Buffer.from("session"), ownerPublicKey.toBuffer()],
  programId,
);
```

The IDL lives at `frontend/src/idl/sentinelfi.json`. Regenerate it after every `anchor build`.

## Checklist: adding a new instruction

```
[ ] Create programs/sentinelfi/src/instructions/<name>.rs
      - #[derive(Accounts)] struct with all constraints
      - pub fn handler(ctx, ...) -> Result<()>
[ ] Add to programs/sentinelfi/src/instructions.rs
      - pub mod <name>;
      - pub use <name>::*;
[ ] Add to programs/sentinelfi/src/lib.rs
      - pub fn <name>(ctx: Context<Name>, ...) -> Result<()> { instructions::<name>::handler(ctx, ...) }
[ ] Add new errors to error.rs (append only, never reorder)
[ ] Run: anchor build
[ ] Run: cp target/idl/sentinelfi.json ../../frontend/src/idl/sentinelfi.json
[ ] Update frontend useSession.ts if the call site changes
[ ] Deploy: anchor deploy (if changing on-chain behavior)
```
