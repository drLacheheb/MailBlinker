from typing import Optional

import httpx

from ...config import settings
from ...domain.entities import OpenEventEntity, TrackedEmailEntity
from ...domain.interfaces import NotificationServiceInterface
from ...logger import get_logger
from ...telemetry import format_elapsed_time

logger = get_logger("telegram.notifier")


class TelegramNotificationService(NotificationServiceInterface):
    def __init__(
        self,
        bot_token: Optional[str] = settings.TELEGRAM_BOT_TOKEN,
        chat_id: Optional[str] = settings.TELEGRAM_CHAT_ID,
    ):
        self._bot_token = bot_token
        self._chat_id = chat_id

    async def send_open_alert(
        self,
        email: TrackedEmailEntity,
        event: OpenEventEntity,
        device: str,
        forwarding_note: Optional[str] = None,
    ) -> None:
        if not self._bot_token or not self._chat_id:
            return

        ip_display = event.ip_address or "Unknown"

        location_parts = [p for p in [event.city, event.region, event.country] if p]
        location_str = ", ".join(location_parts) if location_parts else None

        elapsed_str = (
            f"{format_elapsed_time(event.elapsed_seconds)} after sending"
            if event.elapsed_seconds is not None
            else None
        )

        lines = [
            "<b>Email Opened</b>\n",
            f"<b>Title:</b> {email.title}",
            f"<b>Recipient:</b> {email.recipient_email}",
            f"<b>Device:</b> {device}",
        ]

        if location_str:
            lines.append(f"<b>Location:</b> {location_str}")
        if event.isp:
            lines.append(f"<b>ISP / Network:</b> {event.isp}")
        if event.language:
            lines.append(f"<b>Language:</b> {event.language}")

        lines.append(f"<b>IP:</b> {ip_display}")

        if elapsed_str:
            lines.append(f"<b>Reading Time:</b> Opened {elapsed_str}")

        lines.append(f"<b>Total Opens:</b> {email.open_count}")

        if forwarding_note:
            lines.append(f"\n<b>Forwarding Clue:</b> {forwarding_note}")

        text = "\n".join(lines)

        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Failed to dispatch Telegram push alert: {e}")
