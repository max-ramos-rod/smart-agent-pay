from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SOLANA_PRIVATE_KEY: str
    SOLANA_RPC_URL: str = "https://api.mainnet-beta.solana.com"
    SOLANA_USDC_MINT: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    OPENAI_API_KEY: str | None = None

    USE_AI: bool = False
    AI_TIMEOUT_SECONDS: int = 5

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:8080",
        "http://localhost:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()