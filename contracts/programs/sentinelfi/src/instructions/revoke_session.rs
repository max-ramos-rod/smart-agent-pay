use anchor_lang::prelude::*;
use crate::state::SessionToken;
use crate::error::ErrorCode;
use crate::constants::SESSION_SEED;

#[derive(Accounts)]
pub struct RevokeSession<'info> {
    #[account(mut)]
    pub owner: Signer<'info>,

    #[account(
        mut,
        close = owner,
        seeds = [SESSION_SEED, owner.key().as_ref()],
        bump = session_token.bump,
        has_one = owner @ ErrorCode::NotOwner,
    )]
    pub session_token: Account<'info, SessionToken>,
}

pub fn handler(_ctx: Context<RevokeSession>) -> Result<()> {
    // close = owner transfere os lamports de volta e zera a conta
    Ok(())
}
