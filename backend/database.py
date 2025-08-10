"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import settings

# Create async engine for SQLite
async_engine = create_async_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO, future=True)

# Create sync engine for migrations
sync_engine = create_engine(
    settings.DATABASE_URL.replace("+aiosqlite", ""),
    echo=settings.DATABASE_ECHO,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# Create sync session for migrations
SessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


# Dependency to get async database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Function to create all tables (for development)
async def create_tables():
    # Import here to avoid circular imports
    from models.base import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Function to drop all tables (for development)
async def drop_tables():
    # Import here to avoid circular imports
    from models.base import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
