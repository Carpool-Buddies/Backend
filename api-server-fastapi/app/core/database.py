from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from typing import Generator
from app.core.config import get_settings

settings = get_settings()

# SQLite (used in tests) doesn't support connection-pool sizing args, so only
# pass them for real server databases like Postgres.
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator:
    with SessionLocal() as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
