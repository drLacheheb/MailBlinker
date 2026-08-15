from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from bot.keyboards import (
    delete_confirm_keyboard,
    email_created_inline_keyboard,
    email_detail_keyboard,
    main_menu_keyboard,
    notify_settings_keyboard,
    stats_list_keyboard,
    wizard_step_keyboard,
)
from core import (
    OpenEventEntity,
    TelegramNotificationService,
    TrackedEmailEntity,
)


def test_main_menu_keyboard_layout():
    """Verify persistent 2x2 reply keyboard structure."""
    kb = main_menu_keyboard()
    assert len(kb.keyboard) == 2
    assert kb.keyboard[0][0].text == "⚡ Fast Track"
    assert kb.keyboard[0][1].text == "📝 Compose Email"
    assert kb.keyboard[1][0].text == "📊 My Analytics"
    assert kb.keyboard[1][1].text == "❓ How to Use"
    assert kb.is_persistent is True


def test_email_created_inline_keyboard():
    """Verify action buttons and copy button on created email."""
    kb = email_created_inline_keyboard(pixel_url="https://tracker.com/track/123.gif", email_id=42)
    # Check copy button or action rows
    flat_buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert any(btn.callback_data == "stats:view:42" for btn in flat_buttons if btn.callback_data)
    assert any(
        btn.callback_data == "action:fast_track" for btn in flat_buttons if btn.callback_data
    )


def test_wizard_step_keyboard():
    """Verify skip and cancel buttons in wizard."""
    kb_with_skip = wizard_step_keyboard(can_skip=True)
    flat_buttons = [btn for row in kb_with_skip.inline_keyboard for btn in row]
    assert any(btn.callback_data == "wizard:skip" for btn in flat_buttons)
    assert any(btn.callback_data == "wizard:cancel" for btn in flat_buttons)

    kb_no_skip = wizard_step_keyboard(can_skip=False)
    flat_no_skip = [btn for row in kb_no_skip.inline_keyboard for btn in row]
    assert not any(btn.callback_data == "wizard:skip" for btn in flat_no_skip)
    assert any(btn.callback_data == "wizard:cancel" for btn in flat_no_skip)


def test_stats_keyboards():
    """Verify dashboard email listing, detail controls, and settings keyboards."""
    dummy_emails = [
        TrackedEmailEntity(
            id=1,
            token="tok1",
            title="Pitch to VC",
            recipient_email="vc@fund.com",
            open_count=3,
            created_at=datetime.now(timezone.utc),
        ),
        TrackedEmailEntity(
            id=2,
            token="tok2",
            title="Job Application",
            recipient_email="hr@corp.com",
            open_count=0,
            created_at=datetime.now(timezone.utc),
        ),
    ]

    list_kb = stats_list_keyboard(dummy_emails)
    list_btns = [btn for row in list_kb.inline_keyboard for btn in row]
    assert any(btn.callback_data == "stats:view:1" for btn in list_btns if btn.callback_data)
    assert any(btn.callback_data == "stats:view:2" for btn in list_btns if btn.callback_data)
    assert any(btn.callback_data == "stats:refresh_list" for btn in list_btns if btn.callback_data)

    detail_kb = email_detail_keyboard(1, notify_limit=3, notify_forwarding=True)
    detail_btns = [btn for row in detail_kb.inline_keyboard for btn in row]
    assert any(btn.callback_data == "stats:refresh:1" for btn in detail_btns if btn.callback_data)
    assert any(btn.callback_data == "stats:delete:1" for btn in detail_btns if btn.callback_data)
    assert any(
        btn.callback_data == "stats:settings_menu:1" for btn in detail_btns if btn.callback_data
    )
    assert any(btn.callback_data == "stats:back" for btn in detail_btns if btn.callback_data)

    settings_kb = notify_settings_keyboard(1, current_limit=3, notify_forwarding=True)
    settings_btns = [btn for row in settings_kb.inline_keyboard for btn in row]
    assert any(
        btn.callback_data == "stats:set_limit:1:3" for btn in settings_btns if btn.callback_data
    )
    assert any(
        btn.callback_data == "stats:set_limit:1:none" for btn in settings_btns if btn.callback_data
    )
    assert any(
        btn.callback_data == "stats:toggle_forwarding:1"
        for btn in settings_btns
        if btn.callback_data
    )
    assert any(
        btn.callback_data == "stats:custom_limit:1" for btn in settings_btns if btn.callback_data
    )

    del_kb = delete_confirm_keyboard(1)
    del_btns = [btn for row in del_kb.inline_keyboard for btn in row]
    assert any(
        btn.callback_data == "stats:confirm_delete:1" for btn in del_btns if btn.callback_data
    )


@pytest.mark.asyncio
async def test_rich_notification_alert_formatting():
    """Verify payload contains status badge, expandable quote, and mute/analytics buttons."""
    notifier = TelegramNotificationService(bot_token="test_token")
    email = TrackedEmailEntity(
        id=99,
        token="tok99",
        title="Acquisition Offer",
        recipient_email="founder@startup.com",
        telegram_chat_id="123456",
        open_count=2,
        created_at=datetime.now(timezone.utc),
    )
    event = OpenEventEntity(
        id=1,
        email_id=99,
        timestamp=datetime.now(timezone.utc),
        ip_address="198.51.100.2",
        country="United Kingdom",
        city="London",
        isp="Vodafone Ltd",
        elapsed_seconds=120.0,
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.is_error = False

        await notifier.send_open_alert(
            email=email,
            event=event,
            device="Apple Mail on macOS",
            forwarding_note="Opened on new device",
        )

        assert mock_post.called
        payload = mock_post.call_args[1]["json"]
        text = payload["text"]

        assert "🔥 <b>Email Opened (2x)</b>" in text
        assert "Acquisition Offer" in text
        assert "founder@startup.com" in text
        assert "London, United Kingdom" in text
        assert "<blockquote expandable>" in text
        assert "Vodafone Ltd" in text
        inline_buttons = payload["reply_markup"]["inline_keyboard"][0]
        assert inline_buttons[0]["callback_data"] == "stats:view:99"
        assert inline_buttons[1]["callback_data"] == "stats:quick_mute:99"
