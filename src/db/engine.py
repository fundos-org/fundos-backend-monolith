from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///db.sqlite")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
