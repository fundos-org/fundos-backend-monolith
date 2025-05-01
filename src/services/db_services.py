# app/core/database.py
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os
from src.logging.logging_setup import get_logger 

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")


logger = get_logger(__name__) 

# Async Engine + Session
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"DB session error: {e}")
            raise

# Define function to initialize the database tables
async def init_db():
    """Create the database tables"""
    async with engine.begin() as conn:
        from src.models import Base  # Import your SQLModel base class
        await conn.run_sync(Base.metadata.create_all)
