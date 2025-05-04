from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv

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

async_engine = create_async_engine(
    url = DATABASE_URL, 
    echo=False, 
    future=True
)
