from datetime import timedelta

import pytest
import pytest_asyncio
from core import (
    AsyncSessionLocal,
    CreateEmailDTO,
    CreateEmailUseCase,
    NotificationServiceInterface,
    OpenEventEntity,
    RecordOpenDTO,
    RecordOpenUseCase,
    SqlAlchemyEmailRepository,
    TrackedEmailEntity,
    UpdateNotifySettingsUseCase,
    init_db,
)


class MockNotifier(NotificationServiceInterface):
    def __init__(self):
        self.sent_alerts = []

    async def send_open_alert(
        self,
        email: TrackedEmailEntity,
        event: OpenEventEntity,
        device: str,
        forwarding_note: str | None = None,
    ) -> None:
        self.sent_alerts.append(
            {
                "email_id": email.id,
                "open_count": email.open_count,
                "forwarding_note": forwarding_note,
            }
        )


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    await init_db()


@pytest.mark.asyncio
async def test_notify_limit_enforcement():
    """Verify that push notifications stop once notify_limit is reached."""
    notifier = MockNotifier()

    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        create_uc = CreateEmailUseCase(repo)
        created = await create_uc.execute(
            CreateEmailDTO(
                title="Limit Test",
                recipient_email="limit@test.com",
                telegram_chat_id="123",
            )
        )
        assert created.email.id is not None
        email_id = created.email.id
        token = created.email.token
        base_time = created.email.created_at

        # Set limit to 2 opens
        update_uc = UpdateNotifySettingsUseCase(repo)
        await update_uc.execute(email_id=email_id, limit=2, update_limit=True)

    # 1st Open: Should notify (1 <= 2)
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        record_uc = RecordOpenUseCase(repo, notifier=notifier)
        res1 = await record_uc.execute(
            RecordOpenDTO(
                token=token,
                open_time=base_time + timedelta(seconds=10),
                client_ip="100.1.1.1",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            )
        )
        assert res1.is_recorded is True
        assert len(notifier.sent_alerts) == 1

    # 2nd Open: Should notify (2 <= 2)
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        record_uc = RecordOpenUseCase(repo, notifier=notifier)
        res2 = await record_uc.execute(
            RecordOpenDTO(
                token=token,
                open_time=base_time + timedelta(seconds=20),
                client_ip="100.1.1.1",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            )
        )
        assert res2.is_recorded is True
        assert len(notifier.sent_alerts) == 2

    # 3rd Open (Same device): Should be MUTED (3 > 2)
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        record_uc = RecordOpenUseCase(repo, notifier=notifier)
        res3 = await record_uc.execute(
            RecordOpenDTO(
                token=token,
                open_time=base_time + timedelta(seconds=30),
                client_ip="100.1.1.1",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            )
        )
        assert res3.is_recorded is True
        assert res3.email is not None and res3.email.open_count == 3
        # Alert count should still be 2 (muted!)
        assert len(notifier.sent_alerts) == 2


@pytest.mark.asyncio
async def test_smart_forwarding_override():
    """Verify that a new device triggers an alert even if the limit was reached."""
    notifier = MockNotifier()

    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        create_uc = CreateEmailUseCase(repo)
        created = await create_uc.execute(
            CreateEmailDTO(
                title="Forwarding Test",
                recipient_email="forward@test.com",
                telegram_chat_id="123",
            )
        )
        assert created.email.id is not None
        email_id = created.email.id
        token = created.email.token
        base_time = created.email.created_at

        # Set limit to 1 open and enable forwarding alerts
        update_uc = UpdateNotifySettingsUseCase(repo)
        await update_uc.execute(
            email_id=email_id, limit=1, update_limit=True, notify_forwarding=True
        )

    # 1st Open on iPhone: Should notify (1 <= 1)
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        record_uc = RecordOpenUseCase(repo, notifier=notifier)
        await record_uc.execute(
            RecordOpenDTO(
                token=token,
                open_time=base_time + timedelta(seconds=10),
                client_ip="100.1.1.1",
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
            )
        )
        assert len(notifier.sent_alerts) == 1

    # 2nd Open on SAME iPhone: Should be muted (2 > 1)
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        record_uc = RecordOpenUseCase(repo, notifier=notifier)
        await record_uc.execute(
            RecordOpenDTO(
                token=token,
                open_time=base_time + timedelta(seconds=20),
                client_ip="100.1.1.1",
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
            )
        )
        assert len(notifier.sent_alerts) == 1

    # 3rd Open on NEW DEVICE (Windows): Smart Forwarding Override should trigger!
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        record_uc = RecordOpenUseCase(repo, notifier=notifier)
        await record_uc.execute(
            RecordOpenDTO(
                token=token,
                open_time=base_time + timedelta(seconds=30),
                client_ip="200.2.2.2",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
        )
        # Should have dispatched 3rd alert due to Smart Forwarding Override!
        assert len(notifier.sent_alerts) == 2
        assert notifier.sent_alerts[-1]["forwarding_note"] is not None


@pytest.mark.asyncio
async def test_mute_and_unlimited_policies():
    """Verify limit=0 mutes completely and limit=None allows all."""
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        create_uc = CreateEmailUseCase(repo)
        created = await create_uc.execute(
            CreateEmailDTO(
                title="Mute Policy",
                recipient_email="mute@test.com",
                telegram_chat_id="123",
            )
        )
        assert created.email.id is not None
        email_id = created.email.id

        update_uc = UpdateNotifySettingsUseCase(repo)
        muted_email = await update_uc.execute(email_id=email_id, limit=0, update_limit=True)
        assert muted_email is not None and muted_email.notify_limit == 0

        unlimited_email = await update_uc.execute(email_id=email_id, limit=None, update_limit=True)
        assert unlimited_email is not None and unlimited_email.notify_limit is None

        # Invalid negative limit
        with pytest.raises(ValueError):
            await update_uc.execute(email_id=email_id, limit=-5, update_limit=True)
