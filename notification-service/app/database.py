"""
Database configuration and session management for notification service.
Uses the same PostgreSQL instance as the main application.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database settings loaded from environment variables."""
    database_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://cartographer:cartographer_secret@localhost:5432/cartographer"
    )
    
    class Config:
        env_file = ".env"
        extra = "ignore"


db_settings = DatabaseSettings()

# Create async engine
engine = create_async_engine(
    db_settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models in notification service."""
    pass


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
