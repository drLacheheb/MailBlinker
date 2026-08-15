import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from aiogram.types import Chat, Message, User
from bot.middlewares import UserSyncMiddleware
from core import (
    AsyncSessionLocal,
    CreateEmailDTO,
    CreateEmailUseCase,
    GetUserProfileUseCase,
    SqlAlchemyEmailRepository,
    SqlAlchemyUserRepository,
    UpdateUserPreferencesUseCase,
    UpsertUserDTO,
    UpsertUserUseCase,
    UserEntity,
    init_db,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    await init_db()


@pytest.mark.asyncio
async def test_upsert_user_creation_and_activity_update():
    """Verify creating a new user and updating profile & activity timestamp."""
    chat_id = f"user_{uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyUserRepository(session)
        upsert_uc = UpsertUserUseCase(repo)

        # 1. First onboarding
        user1 = await upsert_uc.execute(
            UpsertUserDTO(
                telegram_chat_id=chat_id,
                telegram_username="alice_dev",
                first_name="Alice",
                last_name="Smith",
                language_code="en",
            )
        )
        assert user1.id is not None
        assert user1.telegram_chat_id == chat_id
        assert user1.telegram_username == "alice_dev"
        assert user1.first_name == "Alice"
        assert user1.is_active is True
        initial_created = user1.created_at
        initial_active = user1.last_active_at

        # 2. Subsequent interaction: updates username and last_active_at
        user2 = await upsert_uc.execute(
            UpsertUserDTO(
                telegram_chat_id=chat_id,
                telegram_username="alice_prime",
                first_name="Alice (Updated)",
            )
        )
        assert user2.id == user1.id
        assert user2.telegram_username == "alice_prime"
        assert user2.first_name == "Alice (Updated)"
        assert user2.created_at == initial_created
        assert user2.last_active_at >= initial_active


@pytest.mark.asyncio
async def test_user_preferences_and_defaults_inheritance():
    """Verify emails inherit user-level default notification preferences and link user_id."""
    chat_id = f"user_{uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as session:
        u_repo = SqlAlchemyUserRepository(session)
        e_repo = SqlAlchemyEmailRepository(session)
        upsert_uc = UpsertUserUseCase(u_repo)
        pref_uc = UpdateUserPreferencesUseCase(u_repo)
        create_email_uc = CreateEmailUseCase(e_repo)

        # Create user
        user = await upsert_uc.execute(UpsertUserDTO(telegram_chat_id=chat_id, first_name="Bob"))
        assert user.id is not None

        # Configure user default preferences: Max 1 alert (1st only) and forwarding alerts OFF
        updated_user = await pref_uc.execute(
            user_id=user.id,
            default_notify_limit=1,
            update_notify_limit=True,
            default_notify_forwarding=False,
        )
        assert updated_user is not None
        assert updated_user.default_notify_limit == 1
        assert updated_user.default_notify_forwarding is False

        # Create email without explicit notify parameters
        created = await create_email_uc.execute(
            CreateEmailDTO(
                title="Default Inheritance Test",
                recipient_email="client@test.com",
                telegram_chat_id=chat_id,
            )
        )

        # Email should automatically inherit user_id and default alert preferences
        assert created.email.user_id == user.id
        assert created.email.notify_limit == 1
        assert created.email.notify_forwarding is False


@pytest.mark.asyncio
async def test_get_user_profile_aggregates():
    """Verify GetUserProfileUseCase aggregates email count and total open metrics."""
    chat_id = f"user_{uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as session:
        u_repo = SqlAlchemyUserRepository(session)
        e_repo = SqlAlchemyEmailRepository(session)
        upsert_uc = UpsertUserUseCase(u_repo)
        create_email_uc = CreateEmailUseCase(e_repo)
        profile_uc = GetUserProfileUseCase(user_repository=u_repo, email_repository=e_repo)

        # Onboard user
        await upsert_uc.execute(UpsertUserDTO(telegram_chat_id=chat_id, first_name="Charlie"))

        # Create 2 emails
        await create_email_uc.execute(
            CreateEmailDTO(
                title="Email 1",
                recipient_email="c1@test.com",
                telegram_chat_id=chat_id,
            )
        )
        await create_email_uc.execute(
            CreateEmailDTO(
                title="Email 2",
                recipient_email="c2@test.com",
                telegram_chat_id=chat_id,
            )
        )

        profile = await profile_uc.execute(telegram_chat_id=chat_id)
        assert profile is not None
        assert profile.user.first_name == "Charlie"
        assert profile.total_emails == 2
        assert profile.total_opens == 0


@pytest.mark.asyncio
async def test_user_sync_middleware():
    """Verify UserSyncMiddleware automatically upserts the user from event_from_user."""
    middleware = UserSyncMiddleware()
    chat_id = 99887766

    tg_user = User(
        id=chat_id,
        is_bot=False,
        first_name="Dana",
        last_name="Scully",
        username="dscully",
        language_code="en",
    )
    chat = Chat(id=chat_id, type="private")
    message = Message(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=chat,
        from_user=tg_user,
        text="/start",
    )

    data = {"event_from_user": tg_user}
    handler_mock = AsyncMock(return_value="handler_result")

    result = await middleware(handler_mock, message, data)
    assert result == "handler_result"
    assert "user" in data
    synced_user = data["user"]
    assert isinstance(synced_user, UserEntity)
    assert synced_user.telegram_chat_id == str(chat_id)
    assert synced_user.first_name == "Dana"
    assert synced_user.telegram_username == "dscully"
