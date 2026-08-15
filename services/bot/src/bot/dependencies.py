from contextlib import asynccontextmanager
from typing import AsyncGenerator

from core import (
    AsyncSessionLocal,
    CreateEmailUseCase,
    DeleteEmailUseCase,
    GetUserProfileUseCase,
    ListEmailsUseCase,
    SqlAlchemyEmailRepository,
    SqlAlchemyUserRepository,
    UpdateNotifySettingsUseCase,
    UpdateUserPreferencesUseCase,
    UpsertUserUseCase,
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
async def get_update_notify_settings_use_case() -> AsyncGenerator[
    UpdateNotifySettingsUseCase, None
]:
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        yield UpdateNotifySettingsUseCase(repository=repo)


@asynccontextmanager
async def get_email_repo() -> AsyncGenerator[SqlAlchemyEmailRepository, None]:
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        yield repo


@asynccontextmanager
async def get_user_repo() -> AsyncGenerator[SqlAlchemyUserRepository, None]:
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyUserRepository(session)
        yield repo


@asynccontextmanager
async def get_upsert_user_use_case() -> AsyncGenerator[UpsertUserUseCase, None]:
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyUserRepository(session)
        yield UpsertUserUseCase(repository=repo)


@asynccontextmanager
async def get_user_profile_use_case() -> AsyncGenerator[GetUserProfileUseCase, None]:
    async with AsyncSessionLocal() as session:
        u_repo = SqlAlchemyUserRepository(session)
        e_repo = SqlAlchemyEmailRepository(session)
        yield GetUserProfileUseCase(user_repository=u_repo, email_repository=e_repo)


@asynccontextmanager
async def get_update_user_preferences_use_case() -> AsyncGenerator[
    UpdateUserPreferencesUseCase, None
]:
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyUserRepository(session)
        yield UpdateUserPreferencesUseCase(repository=repo)
