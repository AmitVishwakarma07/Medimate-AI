"""Database connection and session helper (SQLite for development, Postgres in production)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from . import config

if config.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # pool_pre_ping: test a connection before using it (serverless Postgres closes idle connections).
    # Small pool: free database plans allow only a few connections.
    engine = create_engine(config.DATABASE_URL, pool_pre_ping=True, pool_recycle=300, pool_size=3, max_overflow=2)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """FastAPI dependency: one database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
