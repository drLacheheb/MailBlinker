import html
import io

from aiogram import F, Router, types
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core import CreateEmailDTO

from ..dependencies import get_create_email_use_case
from ..keyboards import email_created_inline_keyboard, wizard_step_keyboard

router = Router()


class FastTrackState(StatesGroup):
    waiting_for_input = State()


async def _process_creation(message: types.Message, title: str, recipient: str):
    if message.bot:
        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    dto = CreateEmailDTO(
        title=title,
        recipient_email=recipient,
        body_text=f"Regarding: {title}",
        telegram_chat_id=str(message.chat.id),
    )

    async with get_create_email_use_case() as use_case:
        result = await use_case.execute(dto)

    safe_title = html.escape(result.email.title)
    safe_email = html.escape(result.email.recipient_email)
    safe_pixel = html.escape(result.pixel_url)

    response_text = (
        f"⚡ <b>Tracker Ready</b>\n\n"
        f"📧 <b>{safe_title}</b>\n"
        f"👤 <code>{safe_email}</code>\n\n"
        f"<code>{safe_pixel}</code>"
    )

    kb = email_created_inline_keyboard(pixel_url=result.pixel_url, email_id=result.email.id)
    await message.answer(response_text, parse_mode="HTML", reply_markup=kb)

    if message.bot:
        await message.bot.send_chat_action(
            chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
        )

    file_bytes = io.BytesIO(result.formatted_html.encode("utf-8"))
    clean_chars = (c for c in title if c.isalnum() or c in (" ", "_", "-"))
    safe_filename_title = "".join(clean_chars).rstrip().replace(" ", "_").lower()
    doc_name = f"email_{safe_filename_title or 'tracked'}.html"
    doc = types.BufferedInputFile(file_bytes.getvalue(), filename=doc_name)
    await message.answer_document(doc, caption="📄 Pasteable Draft")


@router.message(Command("new"))
async def cmd_new(message: types.Message, state: FSMContext):
    raw_text = message.text or ""
    raw_args = raw_text.replace("/new", "").strip()

    if not raw_args:
        await state.set_state(FastTrackState.waiting_for_input)
        prompt = (
            "⚡ <b>Fast Track:</b> Send title and recipient email:\n"
            "<code>Project Proposal | client@company.com</code>"
        )
        await message.answer(
            prompt, parse_mode="HTML", reply_markup=wizard_step_keyboard(can_skip=False)
        )
        return

    parts = [p.strip() for p in raw_args.split("|")]
    title = parts[0] if len(parts) > 0 and parts[0] else "Untitled Email"
    email = parts[1] if len(parts) > 1 and parts[1] else "recipient@example.com"
    await _process_creation(message, title, email)


@router.message(F.text == "⚡ Fast Track")
async def btn_fast_track(message: types.Message, state: FSMContext):
    await state.set_state(FastTrackState.waiting_for_input)
    prompt = (
        "⚡ <b>Fast Track:</b> Send title and recipient email:\n"
        "<code>Project Proposal | client@company.com</code>"
    )
    await message.answer(
        prompt, parse_mode="HTML", reply_markup=wizard_step_keyboard(can_skip=False)
    )


@router.callback_query(F.data == "action:fast_track")
async def callback_fast_track(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(FastTrackState.waiting_for_input)
    prompt = (
        "⚡ <b>Fast Track:</b> Send title and recipient email:\n"
        "<code>Project Proposal | client@company.com</code>"
    )
    if isinstance(callback.message, types.Message):
        await callback.message.answer(
            prompt, parse_mode="HTML", reply_markup=wizard_step_keyboard(can_skip=False)
        )


@router.message(FastTrackState.waiting_for_input)
async def process_fast_track_input(message: types.Message, state: FSMContext):
    raw_text = message.text or ""
    parts = [p.strip() for p in raw_text.split("|")]
    title = parts[0] if len(parts) > 0 and parts[0] else "Untitled Email"
    email = parts[1] if len(parts) > 1 and parts[1] else "recipient@example.com"

    await state.clear()
    await _process_creation(message, title, email)
