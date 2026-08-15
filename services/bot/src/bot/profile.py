from aiogram import Bot
from aiogram.types import BotCommand, MenuButtonCommands
from core import get_logger

logger = get_logger("bot.profile")


async def setup_bot_profile(bot: Bot) -> None:
    """
    Programmatically registers official Telegram Bot metadata:
    - Welcome screen description (shown before pressing 'Start')
    - Profile short bio
    - Native '/' command suggestions menu
    - Bottom-left chat menu button
    """
    try:
        # 1. Welcome Screen Description (Before user starts bot)
        await bot.set_my_description(
            description=(
                "⚡ Welcome to MailBlinker!\n\n"
                "📬 An invisible, unbranded email tracker & Mailtrack alternative.\n\n"
                "✨ Features:\n"
                "• Instant push alerts when your emails are read\n"
                "• Device detection (iPhone, Mac, Android, Windows)\n"
                "• Geolocation & ISP breakdown (City, Country)\n"
                "• Forwarding & multi-device detection\n"
                "• 100% Private (No 'Sent with MailBlinker' branding)\n\n"
                "👉 Tap /start to begin!"
            )
        )

        # 2. Profile Short Description (Bio & share card)
        await bot.set_my_short_description(
            short_description="Invisible email tracker with instant Telegram open alerts."
        )

        # 3. Native Commands Menu
        commands = [
            BotCommand(command="start", description="🚀 Open main menu & quick actions"),
            BotCommand(command="new", description="⚡ Fast track: /new Title | email"),
            BotCommand(command="format", description="📝 4-step interactive email composer"),
            BotCommand(command="stats", description="📊 Live email analytics dashboard"),
            BotCommand(command="cancel", description="❌ Cancel active composer"),
            BotCommand(command="help", description="❓ How to copy-paste into Gmail/Outlook"),
        ]
        await bot.set_my_commands(commands)

        # 4. Chat Menu Button (in chat bar)
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())

        logger.success(
            "Telegram Bot profile and commands successfully synchronized with Telegram API"
        )
    except Exception as exc:
        logger.warning(f"Could not synchronize Telegram bot profile: {exc}")
