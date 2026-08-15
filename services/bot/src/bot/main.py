import asyncio

from aiogram import Bot, Dispatcher
from core import get_logger, init_db, settings

from .handlers import router

logger = get_logger("bot.main")


async def main():
    await init_db()

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN is not configured in .env")
        return

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # Register Telegram bot menu commands
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
    except Exception as e:
        logger.warning(f"Could not register Telegram bot commands menu: {e}")

    logger.success("Telegram Bot started polling")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Telegram Bot session closed")


if __name__ == "__main__":
    asyncio.run(main())
