import html
import io

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from core import CreateEmailDTO
from formatter import EmailLink

from ..dependencies import get_create_email_use_case
from ..states import FormatEmailStates

router = Router()


@router.message(Command("format"))
async def cmd_format(message: types.Message, state: FSMContext):
    await state.set_state(FormatEmailStates.waiting_for_title)
    prompt = (
        "<b>Step 1/5:</b> What is the <b>Subject / Title</b> of this email?\n"
        "<i>(e.g., Application for Backend Engineer, Invoice #1024, Project Update)</i>\n\n"
        "<i>Type <code>/cancel</code> anytime to abort.</i>"
    )
    await message.answer(prompt, parse_mode="HTML")


@router.message(FormatEmailStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    title = (message.text or "").strip()
    await state.update_data(title=title)
    await state.set_state(FormatEmailStates.waiting_for_email)
    prompt = (
        "<b>Step 2/5:</b> What is the <b>Recipient Email</b>?\n"
        "<i>(e.g., client@example.com, hr@company.com)</i>"
    )
    await message.answer(prompt, parse_mode="HTML")


@router.message(FormatEmailStates.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = (message.text or "").strip()
    await state.update_data(email=email)
    await state.set_state(FormatEmailStates.waiting_for_recipient_name)
    prompt = "<b>Step 3/5:</b> What is the <b>Recipient Name</b>? <i>(or type 'skip')</i>"
    await message.answer(prompt, parse_mode="HTML")


@router.message(FormatEmailStates.waiting_for_recipient_name)
async def process_recipient_name(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()
    recipient_name = None if text.lower() == "skip" else text
    await state.update_data(recipient_name=recipient_name)
    await state.set_state(FormatEmailStates.waiting_for_links)
    prompt = (
        "<b>Step 4/5:</b> Enter any <b>Links</b> to include in the email.\n"
        "<i>Format: Label: URL | Label: URL (or type 'skip')</i>\n"
        "<i>Example: Portfolio: https://mysite.com | Resume: https://mysite.com/cv.pdf</i>"
    )
    await message.answer(prompt, parse_mode="HTML")


@router.message(FormatEmailStates.waiting_for_links)
async def process_links(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()
    links_list = []

    if text.lower() != "skip":
        items = [i.strip() for i in text.split("|")]
        for item in items:
            if ":" in item:
                parts = item.split(":", 1)
                label = parts[0].strip()
                url = parts[1].strip()
                if url.startswith("//"):
                    url = "https:" + url
                elif not url.startswith("http://") and not url.startswith("https://"):
                    url = "https://" + url
                links_list.append({"text": label, "url": url})
            elif item:
                links_list.append({"text": item, "url": item})

    await state.update_data(links=links_list)
    await state.set_state(FormatEmailStates.waiting_for_body)
    prompt = "<b>Step 5/5:</b> Enter the <b>Email Body / Message Text</b> (or type 'default'):"
    await message.answer(prompt, parse_mode="HTML")


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
    safe_token = html.escape(result.email.token)
    safe_pixel = html.escape(result.pixel_url)

    response_text = (
        f"<b>Tracked Email Generated</b>\n\n"
        f"<b>Title:</b> {safe_title}\n"
        f"<b>Recipient:</b> <code>{safe_email}</code>\n"
        f"<b>Token:</b> <code>{safe_token}</code>\n\n"
        f"<b>Tracking Pixel URL:</b>\n<code>{safe_pixel}</code>\n"
    )
    await message.answer(response_text, parse_mode="HTML")

    file_bytes = io.BytesIO(result.formatted_html.encode("utf-8"))
    clean_chars = (c for c in title if c.isalnum() or c in (" ", "_", "-"))
    safe_filename_title = "".join(clean_chars).rstrip().replace(" ", "_").lower()
    doc_name = f"email_{safe_filename_title or 'tracked'}.html"
    doc = types.BufferedInputFile(file_bytes.getvalue(), filename=doc_name)
    await message.answer_document(doc, caption="Formatted HTML Email")
