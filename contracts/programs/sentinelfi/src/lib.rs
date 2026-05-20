pub mod constants;
pub mod error;
pub mod instructions;
pub mod state;

use anchor_lang::prelude::*;

pub use constants::*;
pub use instructions::*;
pub use state::*;

declare_id!("HwPkZA1WSussRBD8hgRojJ2bg2Upxa1wr428gBzzoATB");

#[program]
pub mod sentinelfi {
    use super::*;

    pub fn create_session(
        ctx: Context<CreateSession>,
        spending_limit: u64,
        expiry: i64,
    ) -> Result<()> {
        instructions::create_session::handler(ctx, spending_limit, expiry)
    }

    pub fn execute_swap(ctx: Context<ExecuteSwap>, amount: u64) -> Result<()> {
        instructions::execute_swap::handler(ctx, amount)
    }

    pub fn revoke_session(ctx: Context<RevokeSession>) -> Result<()> {
        instructions::revoke_session::handler(ctx)
    }
}
