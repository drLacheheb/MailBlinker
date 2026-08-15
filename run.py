import asyncio
import signal

import uvicorn
from aiogram import Bot, Dispatcher
from bot.handlers import router as bot_router
from core import get_logger, init_db, settings
from tracker.main import app as fastapi_app

logger = get_logger("orchestrator")


async def run_fastapi(stop_event: asyncio.Event):
    config = uvicorn.Config(
        app=fastapi_app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    logger.success(f"FastAPI Tracker API starting on http://{settings.HOST}:{settings.PORT}")

    server_task = asyncio.create_task(server.serve())

    stop_waiter = asyncio.create_task(stop_event.wait())
    done, pending = await asyncio.wait(
        [server_task, stop_waiter],
        return_when=asyncio.FIRST_COMPLETED,
    )

    if stop_waiter in done:
        server.should_exit = True
    else:
        stop_event.set()

    await server_task


async def run_bot_polling(stop_event: asyncio.Event):
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not provided in .env")
        await stop_event.wait()
        return

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(bot_router)

    try:
        from bot.profile import setup_bot_profile
        await setup_bot_profile(bot)
    except Exception as e:
        logger.warning(f"Could not sync profile during polling startup: {e}")

    logger.success("Telegram Bot polling started")
    bot_task = asyncio.create_task(dp.start_polling(bot))

    stop_waiter = asyncio.create_task(stop_event.wait())
    done, pending = await asyncio.wait(
        [bot_task, stop_waiter],
        return_when=asyncio.FIRST_COMPLETED,
    )

    if stop_waiter in done:
        await dp.stop_polling()
    else:
        stop_event.set()

    await bot.session.close()
    try:
        await bot_task
    except Exception:
        pass


async def main():
    logger.info("Initializing MailBlinker")
    await init_db()

    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            # Signal handlers not implemented on Windows event loop
            pass

    tasks = [run_fastapi(stop_event)]

    if settings.is_webhook_mode:
        webhook_ep = f"{settings.BASE_URL}{settings.TELEGRAM_WEBHOOK_PATH}"
        logger.success(f"Telegram operating in Webhook mode at {webhook_ep}")
    elif settings.TELEGRAM_BOT_TOKEN:
        tasks.append(run_bot_polling(stop_event))

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        logger.info("MailBlinker services gracefully stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown requested")
