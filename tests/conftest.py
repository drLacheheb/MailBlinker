import core.infrastructure.db.session as db_session
import pytest_asyncio
from core.infrastructure.db.models import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


@pytest_asyncio.fixture(scope="session", autouse=True)
async def configure_in_memory_db():
    """Configure a global in-memory SQLite engine with StaticPool for the test session."""
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

    # Patch the global session and engine in core
    db_session.engine = test_engine
    db_session.AsyncSessionLocal = test_session_maker

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_db_tables():
    """Wipe and re-create clean tables in memory before each test for complete isolation."""
    async with db_session.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
