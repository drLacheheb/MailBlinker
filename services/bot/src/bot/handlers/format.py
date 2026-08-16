import html
import io

from aiogram import F, Router, types
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from core import CreateEmailDTO
from formatter import EmailLink, detect_text_direction

from ..dependencies import get_create_email_use_case
from ..keyboards import email_created_inline_keyboard, main_menu_keyboard, wizard_step_keyboard
from ..states import FormatEmailStates

router = Router()


@router.message(Command("format"))
@router.message(F.text == "📝 Compose Email")
async def cmd_format(message: types.Message, state: FSMContext):
    await state.set_state(FormatEmailStates.waiting_for_title)
    prompt = "📝 <b>Step 1/3:</b> Enter email Subject / Title:"
    await message.answer(
        prompt, parse_mode="HTML", reply_markup=wizard_step_keyboard(can_skip=False)
    )


@router.callback_query(F.data == "wizard:cancel")
async def callback_wizard_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Wizard cancelled", show_alert=False)
    if isinstance(callback.message, types.Message):
        await callback.message.answer(
            "❌ <b>Cancelled.</b>",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )


@router.message(FormatEmailStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    title = (message.text or "").strip()
    await state.update_data(title=title)
    await state.set_state(FormatEmailStates.waiting_for_email)
    prompt = "👤 <b>Step 2/3:</b> Enter Recipient Email:"
    await message.answer(
        prompt, parse_mode="HTML", reply_markup=wizard_step_keyboard(can_skip=False)
    )


@router.message(FormatEmailStates.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = (message.text or "").strip()
    await state.update_data(email=email)
    await state.set_state(FormatEmailStates.waiting_for_body)
    prompt = "✉️ <b>Step 3/3:</b> Enter Message Body (any URLs will be automatically click-tracked):"
    await message.answer(
        prompt, parse_mode="HTML", reply_markup=wizard_step_keyboard(can_skip=False)
    )


@router.message(FormatEmailStates.waiting_for_body)
async def process_body(message: types.Message, state: FSMContext):
    data = await state.get_data()
    title = data["title"]
    email = data["email"]
    recipient_name = data.get("recipient_name")
    raw_links = data.get("links", [])

    body_text = (message.text or "").strip()
    if body_text.lower() == "default":
        body_text = f"I am writing regarding {title}. Please find the details below."

    if message.bot:
        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    email_links = [EmailLink(text=lnk["text"], url=lnk["url"]) for lnk in raw_links]
    dto = CreateEmailDTO(
        title=title,
        recipient_email=email,
        recipient_name=recipient_name,
        body_text=body_text,
        links=email_links,
        telegram_chat_id=str(message.chat.id),
    )

    async with get_create_email_use_case() as use_case:
        result = await use_case.execute(dto)

    await state.clear()

    safe_title = html.escape(result.email.title)
    safe_email = html.escape(result.email.recipient_email)
    safe_pixel = html.escape(result.pixel_url)

    direction, _ = detect_text_direction(f"{title} {body_text}")
    dir_tag = " [RTL]" if direction == "rtl" else ""

    response_text = (
        f"🎉 <b>Template Ready{dir_tag}</b>\n\n"
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
    doc_name = f"email_{safe_filename_title or 'formatted'}.html"
    doc = types.BufferedInputFile(file_bytes.getvalue(), filename=doc_name)
    await message.answer_document(doc, caption="📄 Pasteable Draft")
