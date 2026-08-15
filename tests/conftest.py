import os

# Set DATABASE_URL to in-memory before loading any core modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import core
import core.infrastructure
import core.infrastructure.db.session as db_session
import pytest_asyncio
from core.infrastructure.db.models import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
test_session_maker = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Patch globally across all core entrypoints
db_session.engine = test_engine
db_session.AsyncSessionLocal = test_session_maker
core.engine = test_engine
core.AsyncSessionLocal = test_session_maker
core.infrastructure.engine = test_engine
core.infrastructure.AsyncSessionLocal = test_session_maker


@pytest_asyncio.fixture(autouse=True)
async def clean_db_tables():
    """Wipe and re-create clean tables in memory before each test for complete isolation."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
