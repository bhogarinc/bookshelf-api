"""Database configuration and session management."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base

from config.settings import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self) -> None:
        self._engine: Optional[AsyncEngine] = None
        self._session_maker: Optional[async_sessionmaker] = None
    
    async def initialize(self) -> None:
        """Initialize database engine and session maker."""
        self._engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=settings.database_echo,
            future=True
        )
        self._session_maker = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        logger.info("Database engine initialized")
    
    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connections closed")
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional scope around a series of operations."""
        if not self._session_maker:
            raise RuntimeError("Database not initialized")
        
        session = self._session_maker()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Session rollback due to: {e}")
            raise
        finally:
            await session.close()
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependency for FastAPI to get database session."""
        async with self.session() as session:
            yield session


db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async for session in db_manager.get_session():
        yield session
