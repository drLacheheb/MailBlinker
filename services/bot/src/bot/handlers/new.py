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
    title = parts[0] if len(parts) > 0 else "Untitled Email"
    email = parts[1] if len(parts) > 1 else "recipient@example.com"

    dto = CreateEmailDTO(
        title=title,
        recipient_email=email,
        body_text=f"Regarding: {title}",
    )

    async with get_create_email_use_case() as use_case:
        result = await use_case.execute(dto)

    response_text = (
        f"<b>Tracked Email Created</b>\n\n"
        f"<b>Title:</b> {result.email.title}\n"
        f"<b>Recipient:</b> <code>{result.email.recipient_email}</code>\n"
        f"<b>Token:</b> <code>{result.email.token}</code>\n\n"
        f"<b>Pixel URL:</b>\n<code>{result.pixel_url}</code>\n"
    )

    await message.answer(response_text, parse_mode="HTML")

    file_bytes = io.BytesIO(result.formatted_html.encode("utf-8"))
    clean_chars = (c for c in title if c.isalnum() or c in (" ", "_", "-"))
    safe_title = "".join(clean_chars).rstrip().replace(" ", "_").lower()
    doc_name = f"email_{safe_title or 'tracked'}.html"
    doc = types.BufferedInputFile(file_bytes.getvalue(), filename=doc_name)
    await message.answer_document(doc, caption="Formatted HTML Email")
