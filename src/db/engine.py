from sqlalchemy.ext.asyncio import create_async_engine
from src.logging.logging_setup import get_logger
import os
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)

def get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value

# USER = get_env("user")
# PASSWORD = get_env("password")
# HOST = get_env("host")
# PORT = get_env("port")
# DBNAME = get_env("dbname")

# DATABASE_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"
DATABASE_URL = "postgresql+asyncpg://fundos:yQHcqyGCkFQ84EodBC1Sc87v4M8dC35M@dpg-d1ohbqc9c44c73fkt7l0-a.oregon-postgres.render.com/fundos"
logger.info(f"Using database URL: {DATABASE_URL}")
async_engine = create_async_engine(
    url = DATABASE_URL, 
    echo=False, 
    future=True
)
