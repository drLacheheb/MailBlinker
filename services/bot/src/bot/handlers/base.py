from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from ..keyboards import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    text = (
        "⚡ <b>MailBlinker</b>\n"
        "Invisible email tracking with instant open alerts.\n\n"
        "Choose an action below to get started:"
    )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
@router.message(F.text == "❓ How to Use")
async def cmd_help(message: types.Message):
    text = (
        "📖 <b>How to Use:</b>\n\n"
        "1. Tap <b>⚡ Fast Track</b> to create your tracker.\n"
        "2. Open the attached <code>.html</code> file in your browser.\n"
        "3. Copy and paste it into your Gmail or Outlook draft.\n"
        "4. When read, you'll receive an instant alert here!"
    )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "No active action to cancel.",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.clear()
    await message.answer(
        "Cancelled.",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
