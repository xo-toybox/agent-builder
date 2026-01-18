"""SQLite database setup and session management."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.config import settings

DATABASE_URL = f"sqlite+aiosqlite:///{settings.database_path}"

engine = create_async_engine(DATABASE_URL, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def init_db():
    """Initialize database tables with WAL mode for better concurrency."""
    # Import models to ensure they're registered with Base
    from backend.infrastructure.persistence.sqlite import models  # noqa: F401

    async with engine.begin() as conn:
        # Enable WAL mode for better concurrency (v0.0.3)
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        # Create all tables including new memory/skills tables
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get database session for dependency injection."""
    async with AsyncSessionLocal() as session:
        yield session
