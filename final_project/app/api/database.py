import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import Any, Optional

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://search:search@postgres/mydatabase")

engine = create_async_engine(DATABASE_URL)
async_sessionmaker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Проверка соединения
async def get_db():
    async with async_sessionmaker() as session:
        yield session