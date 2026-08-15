from contextlib import asynccontextmanager
from typing import AsyncGenerator

from core import (
    AsyncSessionLocal,
    CreateEmailUseCase,
    DeleteEmailUseCase,
    ListEmailsUseCase,
    SqlAlchemyEmailRepository,
)


@asynccontextmanager
async def get_create_email_use_case() -> AsyncGenerator[CreateEmailUseCase, None]:
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        yield CreateEmailUseCase(repository=repo)


@asynccontextmanager
async def get_list_emails_use_case() -> AsyncGenerator[ListEmailsUseCase, None]:
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        yield ListEmailsUseCase(repository=repo)


@asynccontextmanager
async def get_delete_email_use_case() -> AsyncGenerator[DeleteEmailUseCase, None]:
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        yield DeleteEmailUseCase(repository=repo)


@asynccontextmanager
async def get_email_repo() -> AsyncGenerator[SqlAlchemyEmailRepository, None]:
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        yield repo
