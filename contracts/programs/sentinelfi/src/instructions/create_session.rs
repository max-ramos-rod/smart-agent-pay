use anchor_lang::prelude::*;
use crate::state::SessionToken;
use crate::constants::SESSION_SEED;

#[derive(Accounts)]
pub struct CreateSession<'info> {
    #[account(mut)]
    pub owner: Signer<'info>,

    /// CHECK: delegate é o ephemeral pubkey gerado no browser — não precisa ser uma conta existente
    pub delegate: UncheckedAccount<'info>,

    #[account(
        init,
        payer = owner,
        space = SessionToken::LEN,
        seeds = [SESSION_SEED, owner.key().as_ref()],
        bump,
    )]
    pub session_token: Account<'info, SessionToken>,

    pub system_program: Program<'info, System>,
}

pub fn handler(
    ctx: Context<CreateSession>,
    spending_limit: u64,
    expiry: i64,
) -> Result<()> {
    let session = &mut ctx.accounts.session_token;
    session.owner = ctx.accounts.owner.key();
    session.delegate = ctx.accounts.delegate.key();
    session.spending_limit = spending_limit;
    session.amount_spent = 0;
    session.expiry = expiry;
    session.bump = ctx.bumps.session_token;
    Ok(())
}
