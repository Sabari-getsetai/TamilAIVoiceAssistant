"""
Database connection management for Tamil AI Voice Assistant.

This module handles:
- Async SQLAlchemy engine creation
- Session management
- Connection pooling
- Database configuration
- Retry mechanisms with exponential backoff
- Docker service integration
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

# Detect if running in Docker
IS_DOCKER = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER', 'false').lower() == 'true'

# Database configuration with environment variable support
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback construction from individual components if DATABASE_URL not set
    db_user = os.getenv("DB_USER", "tamil_user")
    db_password = os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "tamil_password_dev"))
    db_host = "postgres" if IS_DOCKER else "localhost"
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "tamil_assistant")
    
    DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    logger.info(f"Constructed DATABASE_URL from components for {'Docker' if IS_DOCKER else 'local'} environment")
else:
    logger.info("Using DATABASE_URL from environment variable")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    future=True,
    poolclass=NullPool,  # Use NullPool for development to avoid connection issues
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Usage in FastAPI:
        @app.get("/users/")Task exception was never retrieved
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db session here
            pass
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        # Removed finally block - async context manager handles session.close() automatically


async def wait_for_database(timeout: float = 60.0) -> bool:
    """
    Wait for database to become available.
    
    Args:
        timeout: Maximum time to wait in seconds
        
    Returns:
        bool: True if database is available, False if timeout
    """
    from infrastructure.retry import wait_for_service
    
    logger.info("Waiting for database to become available...")
    return await wait_for_service(
        health_check=check_db_health,
        service_name="PostgreSQL",
        timeout=timeout,
        check_interval=2.0
    )


async def init_db():
    """
    Initialize database by creating all tables.
    This should be called on application startup.
    """
    try:
        from .models import Base

        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            # Enable pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


async def init_db_with_retry(max_retries: int = 5, initial_delay: float = 1.0):
    """
    Initialize database with retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
    """
    from infrastructure.retry import retry_with_backoff, RetryConfig
    
    config = RetryConfig(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True
    )
    
    logger.info("Initializing database with retry logic...")
    
    try:
        # First wait for database to be available
        db_available = await wait_for_database(timeout=60.0)
        
        if not db_available:
            logger.error("Database did not become available within timeout")
            raise ConnectionError("Database connection timeout")
        
        # Then initialize with retry
        await retry_with_backoff(
            operation=init_db,
            config=config,
            operation_name="database_initialization"
        )
        
        logger.info("Database initialized successfully with retry logic")
        
    except Exception as e:
        logger.error(f"Failed to initialize database after retries: {e}")
        raise


async def close_db():
    """
    Close database connections.
    This should be called on application shutdown.
    """
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed")


async def check_db_health() -> bool:
    """
    Check if database connection is healthy.
    Returns True if connection is working, False otherwise.
    """
    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.debug(f"Database health check failed: {e}")
        return False


async def get_db_info() -> dict:
    """
    Get database connection information.
    
    Returns:
        dict: Database connection details
    """
    try:
        async with async_session_factory() as session:
            # Get PostgreSQL version
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            
            # Check pgvector extension
            result = await session.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            )
            has_pgvector = result.scalar()
            
            return {
                "connected": True,
                "version": version,
                "has_pgvector": has_pgvector,
                "url": DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else "unknown",
                "is_docker": IS_DOCKER,
            }
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return {
            "connected": False,
            "error": str(e),
            "is_docker": IS_DOCKER,
        }
