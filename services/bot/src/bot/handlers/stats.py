import html

from aiogram import Router, types
from aiogram.filters import Command

from ..dependencies import get_list_emails_use_case

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    chat_id = str(message.chat.id)
    async with get_list_emails_use_case() as use_case:
        emails = await use_case.execute(limit=10, telegram_chat_id=chat_id)

    if not emails:
        prompt = (
            "No tracked emails found for your account yet. "
            "Create one with <code>/new</code> or <code>/format</code>."
        )
        await message.answer(prompt, parse_mode="HTML")
        return

    lines = ["<b>Your Tracked Emails Telemetry:</b>\n"]
    for e in emails:
        status_text = f"Opened ({e.open_count}x)" if e.open_count > 0 else "Pending"
        if e.first_opened_at:
            first_open_str = e.first_opened_at.strftime("%b %d, %H:%M")
        else:
            first_open_str = "Not yet"

        safe_title = html.escape(e.title)
        safe_recipient = html.escape(e.recipient_email)

        lines.append(
            f"- <b>{safe_title}</b>\n"
            f"  Status: {status_text}\n"
            f"  First Read: {first_open_str}\n"
            f"  To: <code>{safe_recipient}</code>\n"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")
