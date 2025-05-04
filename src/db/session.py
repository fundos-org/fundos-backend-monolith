from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from .engine import async_engine

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to provide the session object"""
    async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
    )
    async with async_session() as session:
        yield session
