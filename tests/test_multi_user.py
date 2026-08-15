from datetime import timedelta
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio
from core import (
    AsyncSessionLocal,
    CreateEmailDTO,
    CreateEmailUseCase,
    ListEmailsUseCase,
    RecordOpenDTO,
    RecordOpenUseCase,
    SqlAlchemyEmailRepository,
    TelegramNotificationService,
    init_db,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_multi_user_email_isolation():
    """Verify that User A and User B only see their own tracked emails."""
    import uuid

    chat_a = f"user_a_{uuid.uuid4().hex[:6]}"
    chat_b = f"user_b_{uuid.uuid4().hex[:6]}"
    chat_c = f"user_c_{uuid.uuid4().hex[:6]}"

    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        create_uc = CreateEmailUseCase(repo)
        list_uc = ListEmailsUseCase(repo)

        # User A creates 2 emails
        await create_uc.execute(
            CreateEmailDTO(
                title="User A Email 1",
                recipient_email="clientA1@example.com",
                telegram_chat_id=chat_a,
            )
        )
        await create_uc.execute(
            CreateEmailDTO(
                title="User A Email 2",
                recipient_email="clientA2@example.com",
                telegram_chat_id=chat_a,
            )
        )

        # User B creates 1 email
        await create_uc.execute(
            CreateEmailDTO(
                title="User B Email 1",
                recipient_email="clientB1@example.com",
                telegram_chat_id=chat_b,
            )
        )

        # Query stats for User A
        user_a_emails = await list_uc.execute(telegram_chat_id=chat_a)
        assert len(user_a_emails) == 2
        assert all(e.telegram_chat_id == chat_a for e in user_a_emails)
        assert {e.title for e in user_a_emails} == {"User A Email 1", "User A Email 2"}

        # Query stats for User B
        user_b_emails = await list_uc.execute(telegram_chat_id=chat_b)
        assert len(user_b_emails) == 1
        assert user_b_emails[0].telegram_chat_id == chat_b
        assert user_b_emails[0].title == "User B Email 1"

        # Query stats for User C (empty)
        user_c_emails = await list_uc.execute(telegram_chat_id=chat_c)
        assert len(user_c_emails) == 0


@pytest.mark.asyncio
async def test_targeted_telegram_notification_dispatch():
    """Verify that open alerts are routed directly to the email creator's telegram_chat_id."""
    notifier = TelegramNotificationService(bot_token="test_token_123")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = httpx.Response(200, json={"ok": True})
        mock_post.return_value = mock_resp

        async with AsyncSessionLocal() as session:
            repo = SqlAlchemyEmailRepository(session)
            create_uc = CreateEmailUseCase(repo)
            record_uc = RecordOpenUseCase(repository=repo, notifier=notifier)

            created = await create_uc.execute(
                CreateEmailDTO(
                    title="Targeted Pitch",
                    recipient_email="investor@vc.com",
                    telegram_chat_id="777888999",
                )
            )

            result = await record_uc.execute(
                RecordOpenDTO(
                    token=created.email.token,
                    open_time=created.email.created_at + timedelta(seconds=30),
                    client_ip="198.51.100.25",
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                )
            )

            assert result.is_recorded is True
            mock_post.assert_called_once()
            called_url = mock_post.call_args[0][0]
            called_json = mock_post.call_args[1]["json"]

            assert "test_token_123" in called_url
            assert called_json["chat_id"] == "777888999"
            assert "Targeted Pitch" in called_json["text"]
            assert "investor@vc.com" in called_json["text"]


@pytest.mark.asyncio
async def test_notification_resilience_on_blocked_bot():
    """Verify that a 403 Forbidden (user blocked bot) does not crash the open recorder."""
    notifier = TelegramNotificationService(bot_token="test_token_123")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Simulate Telegram API returning 403 Forbidden
        mock_resp = httpx.Response(
            403, json={"ok": False, "description": "Forbidden: bot was blocked by the user"}
        )
        mock_post.return_value = mock_resp

        async with AsyncSessionLocal() as session:
            repo = SqlAlchemyEmailRepository(session)
            create_uc = CreateEmailUseCase(repo)
            record_uc = RecordOpenUseCase(repository=repo, notifier=notifier)

            created = await create_uc.execute(
                CreateEmailDTO(
                    title="Blocked User Test",
                    recipient_email="user@blocked.com",
                    telegram_chat_id="999999",
                )
            )

            result = await record_uc.execute(
                RecordOpenDTO(
                    token=created.email.token,
                    open_time=created.email.created_at + timedelta(seconds=30),
                    client_ip="198.51.100.25",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                )
            )

            # The open event should still be successfully recorded in DB despite Telegram 403
            assert result.is_recorded is True
            assert result.email is not None
            assert result.email.open_count == 1


@pytest.mark.asyncio
async def test_email_without_telegram_chat_id_skips_notification():
    """Verify that emails created via raw API without a chat_id record opens safely."""
    notifier = TelegramNotificationService(bot_token="test_token_123")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        async with AsyncSessionLocal() as session:
            repo = SqlAlchemyEmailRepository(session)
            create_uc = CreateEmailUseCase(repo)
            record_uc = RecordOpenUseCase(repository=repo, notifier=notifier)

            created = await create_uc.execute(
                CreateEmailDTO(
                    title="Headless API Email",
                    recipient_email="api@example.com",
                    telegram_chat_id=None,
                )
            )

            result = await record_uc.execute(
                RecordOpenDTO(
                    token=created.email.token,
                    open_time=created.email.created_at + timedelta(seconds=30),
                    client_ip="198.51.100.25",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                )
            )

            assert result.is_recorded is True
            # No notification request sent because no telegram_chat_id was attached
            mock_post.assert_not_called()
