from aiogram import Router, types
from aiogram.filters import Command, CommandStart

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    text = (
        "<b>Gmail Tracker & Email Formatter</b>\n\n"
        "This bot formats any email with invisible open tracking and "
        "sends instant notifications when the recipient opens it.\n\n"
        "<b>Commands:</b>\n"
        "- <code>/new &lt;Title&gt; | &lt;Email&gt;</code> - Fast trackable email\n"
        "- <code>/format</code> - Step-by-step interactive email composer\n"
        "- <code>/stats</code> - View telemetry for all tracked emails\n"
        "- <code>/help</code> - Instructions for Gmail\n"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "<b>Usage Instructions:</b>\n\n"
        "1. Run <code>/new Client Proposal | client@company.com</code> (or <code>/format</code>).\n"
        "2. The bot generates:\n"
        "   - An invisible tracking pixel URL.\n"
        "   - A formatted HTML email (sent as text and as a .html attachment).\n"
        "3. In Gmail:\n"
        "   - Paste the HTML email content into your draft.\n"
        "4. When the recipient opens your email, you will receive a notification here."
    )
    await message.answer(text, parse_mode="HTML")
