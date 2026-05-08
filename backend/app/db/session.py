# backend/app/db/session.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

# =========================
# 🔹 ASYNC (FastAPI)
# =========================

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# =========================
# 🔹 SYNC (Alembic / scripts)
# =========================

SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg")

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)