"""Database configuration module for the Contract Analysis Engine."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from a local .env file.
load_dotenv()

# SQLite is used by default to keep local setup simple for beginners.
# You can set PostgreSQL in .env with:
# DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/contract_engine
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./contract_engine.db")

# The engine is the core SQLAlchemy interface to the database.
# `check_same_thread=False` is required only when using SQLite with FastAPI.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# SessionLocal creates independent database sessions for each request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is inherited by SQLAlchemy models.
Base = declarative_base()


def get_db():
    """Yield a database session for each request and ensure cleanup."""
    db = SessionLocal()
    try:
        # Provide the session to route handlers.
        yield db
    finally:
        # Always close the session to release DB resources.
        db.close()
