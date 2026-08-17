from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ...config import settings
from .models import Base

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Self-healing column synchronization for existing production databases
        if not settings.DATABASE_URL.startswith("sqlite"):
            try:
                await conn.execute(
                    text(
                        "ALTER TABLE tracked_emails "
                        "ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;"
                    )
                )
            except Exception:
                pass
        else:
            try:
                await conn.execute(
                    text("ALTER TABLE tracked_emails ADD COLUMN expires_at DATETIME;")
                )
            except Exception:
                pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
