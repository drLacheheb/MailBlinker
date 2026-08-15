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

    from .profile import setup_bot_profile

    await setup_bot_profile(bot)

    logger.success("Telegram Bot started polling")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Telegram Bot session closed")


if __name__ == "__main__":
    asyncio.run(main())
