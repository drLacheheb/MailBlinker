import html
from typing import Optional

import httpx

from ...config import settings
from ...domain.entities import OpenEventEntity, TrackedEmailEntity
from ...domain.interfaces import NotificationServiceInterface
from ...logger import get_logger
from ...telemetry import format_elapsed_time

logger = get_logger("telegram.notifier")


def _get_device_emoji(device_str: str) -> str:
    lower = device_str.lower()
    if "iphone" in lower or "android" in lower or "mobile" in lower:
        return "📱"
    if "mac" in lower or "apple" in lower or "laptop" in lower:
        return "💻"
    if "windows" in lower or "pc" in lower or "desktop" in lower or "linux" in lower:
        return "🖥️"
    return "🌐"


class TelegramNotificationService(NotificationServiceInterface):
    def __init__(
        self,
        bot_token: Optional[str] = settings.TELEGRAM_BOT_TOKEN,
    ):
        self._bot_token = bot_token

    async def send_open_alert(
        self,
        email: TrackedEmailEntity,
        event: OpenEventEntity,
        device: str,
        forwarding_note: Optional[str] = None,
    ) -> None:
        target_chat_id = email.telegram_chat_id
        if not self._bot_token or not target_chat_id:
            return

        ip_display = html.escape(event.ip_address or "Unknown")
        safe_title = html.escape(email.title)
        safe_recipient = html.escape(email.recipient_email)
        safe_device = html.escape(device)
        dev_emoji = _get_device_emoji(device)

        location_parts = [p for p in [event.city, event.region, event.country] if p]
        location_str = (
            html.escape(", ".join(location_parts)) if location_parts else "Location Hidden / Proxy"
        )

        elapsed_str = (
            f"{format_elapsed_time(event.elapsed_seconds)} after sending"
            if event.elapsed_seconds is not None
            else "Just now"
        )

        # Status badge
        badge = (
            "🟢 <b>Email Opened</b>"
            if email.open_count <= 1
            else f"🔥 <b>Email Opened ({email.open_count}x)</b>"
        )

        lines = [
            f"{badge} • <b>{safe_title}</b>\n",
            f"👤 <code>{safe_recipient}</code>",
            f"{dev_emoji} {safe_device} • 📍 {location_str}",
            f"⏱️ {elapsed_str}",
        ]

        if forwarding_note:
            lines.append(f"\n🔀 <b>Forwarding Alert:</b> {html.escape(forwarding_note)}")

        # Secondary Technical Details in Expandable Quote
        tech_details = [
            f"🌐 <b>IP Address:</b> {ip_display}",
        ]
        if event.isp:
            tech_details.append(f"🏢 <b>ISP / Network:</b> {html.escape(event.isp)}")
        if event.language:
            tech_details.append(f"🗣️ <b>Language:</b> {html.escape(event.language)}")
        tech_details.append(f"🔢 <b>Total Opens:</b> {email.open_count}")

        lines.append(f"\n<blockquote expandable>{chr(10).join(tech_details)}</blockquote>")

        text = "\n".join(lines)

        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": target_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": "📊 View Email Analytics",
                            "callback_data": f"stats:view:{email.id}",
                        }
                    ]
                ]
            }
            if email.id
            else None,
        }

        # Remove None values from payload
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 403:
                    logger.warning(
                        f"Telegram bot was blocked or chat was deleted by user {target_chat_id}"
                    )
                elif resp.status_code == 429:
                    logger.warning(f"Telegram rate limited for user {target_chat_id}: {resp.text}")
                elif resp.is_error:
                    logger.error(f"Telegram API error {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Failed to dispatch Telegram push alert to {target_chat_id}: {e}")
