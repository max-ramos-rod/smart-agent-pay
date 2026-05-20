use anchor_lang::prelude::*;
use crate::state::SessionToken;
use crate::error::ErrorCode;
use crate::constants::SESSION_SEED;

#[derive(Accounts)]
pub struct ExecuteSwap<'info> {
    pub delegate: Signer<'info>,

    /// CHECK: owner é armazenado na session_token — usado só como seed do PDA
    pub owner: UncheckedAccount<'info>,

    #[account(
        mut,
        seeds = [SESSION_SEED, owner.key().as_ref()],
        bump = session_token.bump,
        has_one = delegate @ ErrorCode::Unauthorized,
    )]
    pub session_token: Account<'info, SessionToken>,
}

pub fn handler(ctx: Context<ExecuteSwap>, amount: u64) -> Result<()> {
    let session = &mut ctx.accounts.session_token;
    let clock = Clock::get()?;

    require!(clock.unix_timestamp < session.expiry, ErrorCode::SessionExpired);

    let new_spent = session
        .amount_spent
        .checked_add(amount)
        .ok_or(ErrorCode::SpendingLimitExceeded)?;

    require!(new_spent <= session.spending_limit, ErrorCode::SpendingLimitExceeded);

    session.amount_spent = new_spent;
    Ok(())
}
