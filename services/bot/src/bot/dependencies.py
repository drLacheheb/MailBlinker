from contextlib import asynccontextmanager
from typing import AsyncGenerator

from core import (
    AsyncSessionLocal,
    CreateEmailUseCase,
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
