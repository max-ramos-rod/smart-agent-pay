from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.message import Message
from solders.transaction import Transaction

class SolanaService:
    def __init__(self):
        self.client = AsyncClient("https://api.devnet.solana.com")

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

        tx = Transaction(
            [from_keypair],
            message,
            latest_blockhash.value.blockhash,
        )

        result = await self.client.send_transaction(tx)

        return str(result.value)