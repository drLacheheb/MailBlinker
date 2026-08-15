import html
import io

from aiogram import Router, types
from aiogram.filters import Command
from core import CreateEmailDTO

from ..dependencies import get_create_email_use_case

router = Router()


@router.message(Command("new"))
async def cmd_new(message: types.Message):
    raw_text = message.text or ""
    raw_args = raw_text.replace("/new", "").strip()

    if not raw_args:
        prompt = (
            "<b>Usage:</b>\n<code>/new Title or Subject | recipient@example.com</code>\n\n"
            "<i>Example:</i>\n<code>/new Stripe Application | hr@stripe.com</code>\n"
            "<code>/new Project Proposal | client@acme.com</code>\n\n"
            "Or run <code>/format</code> for interactive mode."
        )
        await message.answer(prompt, parse_mode="HTML")
        return

    parts = [p.strip() for p in raw_args.split("|")]
    title = parts[0] if len(parts) > 0 and parts[0] else "Untitled Email"
    email = parts[1] if len(parts) > 1 and parts[1] else "recipient@example.com"

    dto = CreateEmailDTO(
        title=title,
        recipient_email=email,
        body_text=f"Regarding: {title}",
        telegram_chat_id=str(message.chat.id),
    )

    async with get_create_email_use_case() as use_case:
        result = await use_case.execute(dto)

    safe_title = html.escape(result.email.title)
    safe_email = html.escape(result.email.recipient_email)
    safe_token = html.escape(result.email.token)
    safe_pixel = html.escape(result.pixel_url)

    response_text = (
        f"<b>Tracked Email Created</b>\n\n"
        f"<b>Title:</b> {safe_title}\n"
        f"<b>Recipient:</b> <code>{safe_email}</code>\n"
        f"<b>Token:</b> <code>{safe_token}</code>\n\n"
        f"<b>Pixel URL:</b>\n<code>{safe_pixel}</code>\n"
    )

    await message.answer(response_text, parse_mode="HTML")

    file_bytes = io.BytesIO(result.formatted_html.encode("utf-8"))
    clean_chars = (c for c in title if c.isalnum() or c in (" ", "_", "-"))
    safe_filename_title = "".join(clean_chars).rstrip().replace(" ", "_").lower()
    doc_name = f"email_{safe_filename_title or 'tracked'}.html"
    doc = types.BufferedInputFile(file_bytes.getvalue(), filename=doc_name)
    await message.answer_document(doc, caption="Formatted HTML Email")
