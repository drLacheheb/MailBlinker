import html
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

        location_parts = [p for p in [event.city, event.region, event.country] if p]
        location_str = (
            html.escape(", ".join(location_parts)) if location_parts else None
        )

        elapsed_str = (
            f"{format_elapsed_time(event.elapsed_seconds)} after sending"
            if event.elapsed_seconds is not None
            else None
        )

        lines = [
            "<b>Email Opened</b>\n",
            f"<b>Title:</b> {safe_title}",
            f"<b>Recipient:</b> <code>{safe_recipient}</code>",
            f"<b>Device:</b> {safe_device}",
        ]

        if location_str:
            lines.append(f"<b>Location:</b> {location_str}")
        if event.isp:
            lines.append(f"<b>ISP / Network:</b> {html.escape(event.isp)}")
        if event.language:
            lines.append(f"<b>Language:</b> {html.escape(event.language)}")

        lines.append(f"<b>IP:</b> {ip_display}")

        if elapsed_str:
            lines.append(f"<b>Reading Time:</b> Opened {elapsed_str}")

        lines.append(f"<b>Total Opens:</b> {email.open_count}")

        if forwarding_note:
            lines.append(f"\n<b>Forwarding Clue:</b> {html.escape(forwarding_note)}")

        text = "\n".join(lines)

        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": target_chat_id,
            "text": text,
            "parse_mode": "HTML",
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 403:
                    logger.warning(
                        f"Telegram bot was blocked or chat was deleted by user {target_chat_id}"
                    )
                elif resp.status_code == 429:
                    logger.warning(
                        f"Telegram rate limited when sending alert to user {target_chat_id}: {resp.text}"
                    )
                elif resp.is_error:
                    logger.error(
                        f"Telegram API returned error {resp.status_code}: {resp.text}"
                    )
        except Exception as e:
            logger.error(f"Failed to dispatch Telegram push alert to {target_chat_id}: {e}")
