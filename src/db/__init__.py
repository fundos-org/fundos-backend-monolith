from src.logging.logging_setup import get_logger
from sqlmodel import SQLModel
from .engine import async_engine

logger = get_logger(__name__)

async def init_db():
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database connection successful and schema initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize the database, error: {e}", exc_info=True)
