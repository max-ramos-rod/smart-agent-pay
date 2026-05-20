use anchor_lang::prelude::*;

#[error_code]
pub enum ErrorCode {
    #[msg("Session has expired")]
    SessionExpired,
    #[msg("Spending limit exceeded")]
    SpendingLimitExceeded,
    #[msg("Not authorized: caller is not the delegate")]
    Unauthorized,
    #[msg("Not authorized: caller is not the session owner")]
    NotOwner,
}
