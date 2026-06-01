from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.message import Message
from solders.transaction import Transaction
from solders.instruction import Instruction, AccountMeta

_TOKEN_PROGRAM       = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
_ASSOC_TOKEN_PROGRAM = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJe1bm")
_SYSTEM_PROGRAM      = Pubkey.from_string("11111111111111111111111111111111")


def _get_ata(wallet: Pubkey, mint: Pubkey) -> Pubkey:
    ata, _ = Pubkey.find_program_address(
        [bytes(wallet), bytes(_TOKEN_PROGRAM), bytes(mint)],
        _ASSOC_TOKEN_PROGRAM,
    )
    return ata


def _make_create_ata_ix(payer: Pubkey, ata: Pubkey, owner: Pubkey, mint: Pubkey) -> Instruction:
    return Instruction(
        program_id=_ASSOC_TOKEN_PROGRAM,
        accounts=[
            AccountMeta(pubkey=payer, is_signer=True, is_writable=True),
            AccountMeta(pubkey=ata, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner, is_signer=False, is_writable=False),
            AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=_SYSTEM_PROGRAM, is_signer=False, is_writable=False),
            AccountMeta(pubkey=_TOKEN_PROGRAM, is_signer=False, is_writable=False),
        ],
        data=bytes([]),
    )


def _make_transfer_checked_ix(
    source: Pubkey, mint: Pubkey, dest: Pubkey, authority: Pubkey,
    amount: int, decimals: int,
) -> Instruction:
    # discriminant 12 = TransferChecked no SPL Token Program
    data = bytes([12]) + amount.to_bytes(8, "little") + bytes([decimals])
    return Instruction(
        program_id=_TOKEN_PROGRAM,
        accounts=[
            AccountMeta(pubkey=source, is_signer=False, is_writable=True),
            AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=dest, is_signer=False, is_writable=True),
            AccountMeta(pubkey=authority, is_signer=True, is_writable=False),
        ],
        data=data,
    )


class SolanaService:
    def __init__(self):
        from app.core.config import settings
        self.client = AsyncClient(settings.SOLANA_RPC_URL)
        self.usdc_mint = Pubkey.from_string(settings.SOLANA_USDC_MINT)

    async def transfer_sol(
        self,
        from_keypair: Keypair,
        to_pubkey: str,
        amount_sol: float,
    ) -> str:
        lamports = int(amount_sol * 1_000_000_000)
        latest_blockhash = await self.client.get_latest_blockhash()

        instruction = transfer(
            TransferParams(
                from_pubkey=from_keypair.pubkey(),
                to_pubkey=Pubkey.from_string(to_pubkey),
                lamports=lamports,
            )
        )

        message = Message.new_with_blockhash(
            [instruction],
            from_keypair.pubkey(),
            latest_blockhash.value.blockhash,
        )
        tx = Transaction([from_keypair], message, latest_blockhash.value.blockhash)
        result = await self.client.send_transaction(tx)
        return str(result.value)

    async def transfer_usdc(
        self,
        from_keypair: Keypair,
        to_pubkey: str,
        amount_usdc: float,
    ) -> str:
        DECIMALS = 6
        from_pk = from_keypair.pubkey()
        to_pk = Pubkey.from_string(to_pubkey)

        from_ata = _get_ata(from_pk, self.usdc_mint)
        to_ata = _get_ata(to_pk, self.usdc_mint)

        latest_blockhash = await self.client.get_latest_blockhash()
        instructions = []

        to_ata_info = await self.client.get_account_info(to_ata)
        if to_ata_info.value is None:
            instructions.append(_make_create_ata_ix(from_pk, to_ata, to_pk, self.usdc_mint))

        amount_raw = int(amount_usdc * 10 ** DECIMALS)
        instructions.append(
            _make_transfer_checked_ix(from_ata, self.usdc_mint, to_ata, from_pk, amount_raw, DECIMALS)
        )

        message = Message.new_with_blockhash(
            instructions,
            from_pk,
            latest_blockhash.value.blockhash,
        )
        tx = Transaction([from_keypair], message, latest_blockhash.value.blockhash)
        result = await self.client.send_transaction(tx)
        return str(result.value)
