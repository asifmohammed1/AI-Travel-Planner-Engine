"""
Database configuration and session management.
Supports both Google Cloud SQL (production) and local PostgreSQL (development).
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./travel_planner_dev.db")

# Use NullPool for Cloud SQL (Cloud SQL Proxy handles connection pooling)
if "cloudsql" in DATABASE_URL or "postgresql" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        echo=False,
        connect_args={"connect_timeout": 10},
    )
else:
    # SQLite for local development fallback
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    except Exception as exc:
        logger.error(f"Database session error: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create all tables defined in models."""
    from models import Base as ModelBase  # noqa: F401 – triggers model registration
    ModelBase.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified.")
