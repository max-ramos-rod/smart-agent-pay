import asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.services.wallet.repository import WalletRepository

class WalletService:
    def __init__(self, repository: WalletRepository | None = None):
        self.repository = repository or WalletRepository()

    async def connect_wallet(self, db: AsyncSession, user_id: int, public_key: str):
        public_key = public_key.strip()

        wallet = await self.repository.get_by_public_key(db, public_key)

        if wallet:
            if wallet.user_id != user_id:
                raise HTTPException(status_code=400, detail="Wallet already in use")
            return wallet

        new_wallet = self.repository.model(
            user_id=user_id,
            public_key=public_key,
        )

        await self.repository.create(db, new_wallet)
        return new_wallet

    async def list_user_wallets(self, db: AsyncSession, user_id: int):
        return await self.repository.get_by_user(db, user_id)

    async def get_user_wallet(self, db: AsyncSession, user_id: int):
        wallets = await self.repository.get_by_user(db, user_id)

        if not wallets:
            raise HTTPException(status_code=404, detail="User has no wallet")

        if len(wallets) > 1:
            raise HTTPException(
                status_code=400,
                detail="Multiple wallets, specify wallet_id"
            )

        return wallets[0]

    async def get_user_wallet_by_id(
        self,
        db: AsyncSession,
        user_id: int,
        wallet_id: int
    ):
        wallet = await self.repository.get(db, wallet_id)

        if not wallet or wallet.user_id != user_id:
            raise HTTPException(status_code=404, detail="Wallet not found")

        return wallet

    async def get_balance(self, public_key: str):
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(
                "https://api.devnet.solana.com",
                json={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [public_key]}
            )
            lamports = r.json()["result"]["value"]
            return {"balance": round(lamports / 1_000_000_000, 4)}

    async def get_usdc_balance(self, public_key: str) -> float:
        USDC_MINT = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(
                "https://api.devnet.solana.com",
                json={
                    "jsonrpc": "2.0", "id": 1,
                    "method": "getTokenAccountsByOwner",
                    "params": [public_key, {"mint": USDC_MINT}, {"encoding": "jsonParsed"}],
                }
            )
            accounts = r.json().get("result", {}).get("value", [])
            if not accounts:
                return 0.0
            return float(accounts[0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"] or 0)

    async def get_all_balances(self, public_key: str) -> dict:
        sol, usdc = await asyncio.gather(
            self.get_balance(public_key),
            self.get_usdc_balance(public_key),
        )
        return {"sol": sol["balance"], "usdc": usdc}
    
    async def get_user_wallet_by_address(
        self,
        db: AsyncSession,
        user_id: int,
        public_key: str,
    ):
        wallet = await self.repository.get_by_public_key(db, public_key)

        if not wallet or wallet.user_id != user_id:
            raise HTTPException(status_code=404, detail="Wallet not found")

        return wallet    