import asyncio

import uvicorn
from aiogram import Bot, Dispatcher
from bot.handlers import router as bot_router
from core import get_logger, init_db, settings
from tracker.main import app as fastapi_app

logger = get_logger("orchestrator")


async def run_fastapi():
    config = uvicorn.Config(
        app=fastapi_app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    logger.success(f"FastAPI Tracker API starting on http://{settings.HOST}:{settings.PORT}")
    await server.serve()


async def run_bot():
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not provided in .env")
        return

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(bot_router)

    logger.success("Telegram Bot polling started")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def main():
    logger.info("Initializing MailBlinker (Tracker API & Telegram Bot)")
    await init_db()

    await asyncio.gather(
        run_fastapi(),
        run_bot(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
