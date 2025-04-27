from contextlib import asynccontextmanager
from fastapi import FastAPI
from services.db_services import DatabaseServices

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to initialize the database before the application starts
    and close the session after the application shuts down.
    """
    db_service = DatabaseServices()
    db_service.init_db()  # Initialize the database
    yield
    db_service.SessionLocal.remove()  # Close the session 
