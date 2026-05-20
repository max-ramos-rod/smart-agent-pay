use {
    anchor_lang::{solana_program::instruction::Instruction, InstructionData, ToAccountMetas},
    litesvm::LiteSVM,
    solana_message::{Message, VersionedMessage},
    solana_signer::Signer,
    solana_keypair::Keypair,
    solana_transaction::versioned::VersionedTransaction,
};

#[test]
fn test_create_session() {
    let program_id = sentinelfi::id();
    let owner = Keypair::new();
    let delegate = Keypair::new();
    let mut svm = LiteSVM::new();
    let bytes = include_bytes!("../../../target/deploy/sentinelfi.so");
    svm.add_program(program_id, bytes).unwrap();
    svm.airdrop(&owner.pubkey(), 1_000_000_000).unwrap();

    let spending_limit: u64 = 50_000_000; // 50 USDC
    let expiry: i64 = 9_999_999_999;      // muito no futuro

    let (session_pda, _bump) = anchor_lang::prelude::Pubkey::find_program_address(
        &[b"session", owner.pubkey().as_ref()],
        &program_id,
    );

    let instruction = Instruction::new_with_bytes(
        program_id,
        &sentinelfi::instruction::CreateSession { spending_limit, expiry }.data(),
        sentinelfi::accounts::CreateSession {
            owner: owner.pubkey(),
            delegate: delegate.pubkey(),
            session_token: session_pda,
            system_program: anchor_lang::solana_program::system_program::id(),
        }
        .to_account_metas(None),
    );

    let blockhash = svm.latest_blockhash();
    let msg = Message::new_with_blockhash(&[instruction], Some(&owner.pubkey()), &blockhash);
    let tx = VersionedTransaction::try_new(VersionedMessage::Legacy(msg), &[owner]).unwrap();

    let res = svm.send_transaction(tx);
    assert!(res.is_ok(), "create_session falhou: {:?}", res.err());
}
