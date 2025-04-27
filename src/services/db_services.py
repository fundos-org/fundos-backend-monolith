from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os
from logging.logging_setup import get_logger

class DatabaseServices:
    def __init__(self, db_url: str = "sqlite:///./test.db"):
        self.db_url = db_url
        self.engine = create_engine(self.db_url, echo=True, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine, class_=Session)
        self.logger = get_logger("DatabaseServices", env="dev")

    def init_db(self) -> None:
        """
        Initialize the database by creating tables if they don't exist.
        """
        if not os.path.exists(self.db_url[10:]):  # Check if SQLite file exists
            self.logger.info("Database file does not exist. Creating new database.")
            SQLModel.metadata.create_all(self.engine)
            self.logger.info("Database and tables created successfully.")
        else:
            self.logger.info("Database file exists. Skipping creation.")

    def get_session(self) -> Generator[Session, None, None]:
        """
        Dependency that provides a database session.
        """
        with self.SessionLocal() as session:
            yield session
