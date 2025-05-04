from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv
import asyncio 
import logging 

logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)

load_dotenv()

def get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value

USER = get_env("user")
PASSWORD = get_env("password")
HOST = get_env("host")
PORT = get_env("port")
DBNAME = get_env("dbname")

DATABASE_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

# DATABASE_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"
logger.info(DATABASE_URL)
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///db.sqlite")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async def test_connection():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: print("Successfully connected to the database!"))
    except Exception as e:
        print(f"Failed to connect to the database: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())