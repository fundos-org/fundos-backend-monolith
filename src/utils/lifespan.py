from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.db import init_db
from src.logging.logging_setup import get_logger
from src.db.engine import async_engine

logger = get_logger(__name__)


@asynccontextmanager 
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to initialize the database before the application starts
    and close the session after the application shuts down.
    """
    db_instance = await init_db()  # Initialize the database
    logger.info(db_instance)
    yield
    await async_engine.dispose() # Close the session 


