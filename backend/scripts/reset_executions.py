# scripts/reset_executions.py

from app.db.session import AsyncSessionLocal
from sqlalchemy import text
import asyncio

async def run():
    async with AsyncSessionLocal() as db:
        await db.execute(text("TRUNCATE TABLE executions RESTART IDENTITY CASCADE"))
        await db.commit()
        print("✅ executions resetadas")

asyncio.run(run())