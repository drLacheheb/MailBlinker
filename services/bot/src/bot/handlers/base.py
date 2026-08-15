from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    text = (
        "<b>Gmail Tracker & Email Formatter</b>\n\n"
        "This bot formats any email with invisible open tracking and "
        "sends instant notifications to you when the recipient opens it.\n\n"
        "<b>Commands:</b>\n"
        "- <code>/new &lt;Title&gt; | &lt;Email&gt;</code> - Fast trackable email\n"
        "- <code>/format</code> - Step-by-step interactive email composer\n"
        "- <code>/stats</code> - View telemetry for your tracked emails\n"
        "- <code>/cancel</code> - Cancel active composer wizard\n"
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
        "3. In Gmail / Outlook:\n"
        "   - Paste the HTML email content into your draft.\n"
        "4. When the recipient opens your email, you will receive an instant notification here.\n"
        "5. Type <code>/stats</code> anytime to view your email opens."
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("No active action to cancel.", parse_mode="HTML")
        return

    await state.clear()
    await message.answer("Action cancelled. Run <code>/new</code> or <code>/format</code> to start fresh.", parse_mode="HTML")
