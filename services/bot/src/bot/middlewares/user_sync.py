from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from core import UpsertUserDTO

from ..dependencies import get_upsert_user_use_case


class UserSyncMiddleware(BaseMiddleware):
    """Outer middleware to auto-sync Telegram user profile & last active timestamp."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        event_user: User | None = data.get("event_from_user")
        if event_user and not event_user.is_bot:
            try:
                dto = UpsertUserDTO(
                    telegram_chat_id=str(event_user.id),
                    telegram_username=event_user.username,
                    first_name=event_user.first_name,
                    last_name=event_user.last_name,
                    language_code=event_user.language_code,
                )
                async with get_upsert_user_use_case() as use_case:
                    user_entity = await use_case.execute(dto)
                    data["user"] = user_entity
            except Exception:
                # Do not block bot interactions if user sync fails
                pass

        return await handler(event, data)
