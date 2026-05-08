from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SOLANA_PRIVATE_KEY: str
    OPENAI_API_KEY: str | None = None
    USE_AI: bool = False
    AI_TIMEOUT_SECONDS: int = 5    
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"


settings = Settings()