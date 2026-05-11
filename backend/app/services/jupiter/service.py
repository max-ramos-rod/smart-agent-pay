import httpx

JUPITER_QUOTE_URL = "https://quote-api.jup.ag/v6/quote"
JUPITER_SWAP_URL = "https://quote-api.jup.ag/v6/swap"

LAMPORTS_PER_SOL = 1_000_000_000
USDC_DECIMALS = 6

# Mainnet mint addresses — Jupiter opera em mainnet
TOKEN_MINTS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
}


class JupiterService:
    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: float,
        slippage_bps: int = 50,
    ) -> dict:
        input_mint = TOKEN_MINTS[token_in]
        output_mint = TOKEN_MINTS[token_out]

        if token_in == "SOL":
            amount_raw = int(amount_in * LAMPORTS_PER_SOL)
        else:
            amount_raw = int(amount_in * (10**USDC_DECIMALS))

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                JUPITER_QUOTE_URL,
                params={
                    "inputMint": input_mint,
                    "outputMint": output_mint,
                    "amount": str(amount_raw),
                    "slippageBps": str(slippage_bps),
                },
            )
            resp.raise_for_status()
            data = resp.json()

        if "error" in data:
            raise ValueError(f"Jupiter quote error: {data['error']}")

        return data

    async def get_swap_tx(
        self,
        quote_response: dict,
        user_public_key: str,
    ) -> str:
        """Retorna base64 de uma VersionedTransaction para o usuário assinar."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                JUPITER_SWAP_URL,
                json={
                    "quoteResponse": quote_response,
                    "userPublicKey": user_public_key,
                    "wrapAndUnwrapSol": True,
                    "dynamicComputeUnitLimit": True,
                    "prioritizationFeeLamports": "auto",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return data["swapTransaction"]

    async def get_quote_safe(
        self,
        token_in: str,
        token_out: str,
        amount_in: float,
        slippage_bps: int = 50,
    ) -> dict | None:
        """Tenta obter quote real; retorna None se falhar (devnet/offline)."""
        try:
            return await self.get_quote(token_in, token_out, amount_in, slippage_bps)
        except Exception as e:
            print(f"⚠️ Jupiter quote falhou (mock mode): {e}")
            return None

    def mock_quote(self, token_in: str, token_out: str, amount_in: float) -> dict:
        """Quote simulado para demo no devnet."""
        if token_in == "SOL" and token_out == "USDC":
            out_raw = int(amount_in * 150 * (10 ** USDC_DECIMALS))  # ~$150/SOL fictício
        elif token_in == "USDC" and token_out == "SOL":
            out_raw = int((amount_in / 150) * LAMPORTS_PER_SOL)
        else:
            out_raw = 0
        return {"outAmount": str(out_raw), "_mock": True}

    def format_out_amount(self, quote: dict, token_out: str) -> str:
        raw = int(quote.get("outAmount", 0))
        if token_out == "SOL":
            return f"{raw / LAMPORTS_PER_SOL:.4f} SOL"
        return f"{raw / (10 ** USDC_DECIMALS):.2f} USDC"
