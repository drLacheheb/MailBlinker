from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from bot.handlers import router as bot_router
from core import get_logger, settings
from fastapi import APIRouter, Header, HTTPException, Request, Response, status

logger = get_logger("tracker.webhook")

router = APIRouter(tags=["Webhook"])

bot_instance: Optional[Bot] = None
dp_instance: Optional[Dispatcher] = None


def get_bot() -> Optional[Bot]:
    global bot_instance
    if bot_instance is None and settings.TELEGRAM_BOT_TOKEN:
        bot_instance = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    return bot_instance


def get_dispatcher() -> Dispatcher:
    global dp_instance
    if dp_instance is None:
        dp_instance = Dispatcher()
        dp_instance.include_router(bot_router)
    return dp_instance


async def setup_webhook() -> None:
    """Register Telegram webhook with Telegram API on app startup."""
    bot = get_bot()
    if not bot or not settings.is_webhook_mode:
        return

    dp = get_dispatcher()
    webhook_url = f"{settings.BASE_URL.rstrip('/')}{settings.TELEGRAM_WEBHOOK_PATH}"

    logger.info(f"Registering Telegram Webhook at: {webhook_url}")
    try:
        from aiogram.types import BotCommand
        commands = [
            BotCommand(command="start", description="Start bot & show guide"),
            BotCommand(command="new", description="Fast tracked email (/new Title | email)"),
            BotCommand(command="format", description="Interactive 5-step email composer"),
            BotCommand(command="stats", description="View your email open analytics"),
            BotCommand(command="cancel", description="Cancel active email composer"),
            BotCommand(command="help", description="How to use with Gmail/Outlook"),
        ]
        await bot.set_my_commands(commands)
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
            drop_pending_updates=False,
            allowed_updates=dp.resolve_used_update_types(),
        )
        logger.success(f"Telegram Webhook successfully configured on {webhook_url}")
    except Exception as exc:
        logger.error(f"Failed to configure Telegram Webhook: {exc}")


async def close_webhook_bot() -> None:
    """Clean up bot session on app shutdown."""
    global bot_instance
    if bot_instance:
        await bot_instance.session.close()
        bot_instance = None
        logger.info("Telegram Webhook Bot session closed")


@router.post(settings.TELEGRAM_WEBHOOK_PATH)
async def telegram_webhook_endpoint(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
):
    """Receive and dispatch incoming Telegram updates via Webhook."""
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning("Rejected Telegram Webhook update: invalid secret token")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Telegram secret token",
            )

    bot = get_bot()
    if not bot:
        return Response(status_code=status.HTTP_200_OK)

    dp = get_dispatcher()
    try:
        raw_update = await request.json()
        update = Update.model_validate(raw_update, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as exc:
        logger.error(f"Error processing Telegram Webhook update: {exc}")

    return Response(status_code=status.HTTP_200_OK)
