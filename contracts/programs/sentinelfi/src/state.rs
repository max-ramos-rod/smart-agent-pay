use anchor_lang::prelude::*;

#[account]
pub struct SessionToken {
    pub owner: Pubkey,          // wallet do usuário (Phantom)
    pub delegate: Pubkey,       // ephemeral pubkey gerado no browser
    pub spending_limit: u64,    // em micro-USDC (6 decimais, ex: 50_000_000 = 50 USDC)
    pub amount_spent: u64,      // acumulador verificado em execute_swap
    pub expiry: i64,            // Unix timestamp UTC
    pub bump: u8,               // PDA bump seed
}

impl SessionToken {
    pub const LEN: usize = 8   // discriminator
        + 32  // owner
        + 32  // delegate
        + 8   // spending_limit
        + 8   // amount_spent
        + 8   // expiry
        + 1;  // bump
}
