import html

from aiogram import F, Router, types
from aiogram.filters import Command

from ..dependencies import get_delete_email_use_case, get_email_repo, get_list_emails_use_case
from ..keyboards import (
    delete_confirm_keyboard,
    email_detail_keyboard,
    main_menu_keyboard,
    stats_list_keyboard,
)

router = Router()


def _format_dashboard_text(emails) -> str:
    if not emails:
        return (
            "📊 <b>Analytics:</b> No tracked emails yet.\n"
            "Tap <b>⚡ Fast Track</b> to create your first tracker!"
        )

    opened_count = sum(1 for e in emails if e.open_count > 0)
    total_opens = sum(e.open_count for e in emails)

    return (
        f"📊 <b>Analytics</b> • {opened_count}/{len(emails)} Read ({total_opens} opens)\n"
        "Select an email below to view telemetry:"
    )


def _format_detail_text(email) -> str:
    safe_title = html.escape(email.title)
    safe_recipient = html.escape(email.recipient_email)
    status_icon = "🟢" if email.open_count > 0 else "⏳"
    status_text = f"Read {email.open_count}x" if email.open_count > 0 else "Pending"

    lines = [
        f"{status_icon} <b>{safe_title}</b>",
        f"👤 <code>{safe_recipient}</code> • {status_text}",
    ]

    if email.first_opened_at:
        first_open_str = email.first_opened_at.strftime("%b %d, %H:%M UTC")
        lines.append(f"⏱️ First read: {first_open_str}")
    if email.last_opened_at and email.open_count > 1:
        last_open_str = email.last_opened_at.strftime("%b %d, %H:%M UTC")
        lines.append(f"🔄 Last activity: {last_open_str}")

    if not email.events:
        lines.append("\n<i>No opens recorded yet.</i>")
    else:
        lines.append("\n<b>Recent Open Events:</b>")
        for i, ev in enumerate(reversed(email.events[-5:]), 1):
            time_str = ev.timestamp.strftime("%b %d, %H:%M")
            loc_parts = [p for p in [ev.city, ev.country] if p]
            loc_str = ", ".join(loc_parts) if loc_parts else "Location Hidden"
            dev = ev.device_model or ev.browser_name or "Web Client"
            event_num = len(email.events) - i + 1

            lines.append(
                f"• <b>#{event_num}</b> {time_str} • {html.escape(dev)} • 📍 {html.escape(loc_str)}"
            )

    return "\n".join(lines)


@router.message(Command("stats"))
@router.message(F.text == "📊 My Analytics")
async def cmd_stats(message: types.Message):
    chat_id = str(message.chat.id)
    async with get_list_emails_use_case() as use_case:
        emails = await use_case.execute(limit=10, telegram_chat_id=chat_id)

    text = _format_dashboard_text(emails)
    kb = stats_list_keyboard(emails) if emails else main_menu_keyboard()
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "stats:refresh_list")
async def callback_refresh_list(callback: types.CallbackQuery):
    chat_id = str(callback.from_user.id)
    async with get_list_emails_use_case() as use_case:
        emails = await use_case.execute(limit=10, telegram_chat_id=chat_id)

    text = _format_dashboard_text(emails)
    kb = stats_list_keyboard(emails)

    await callback.answer("✅ Dashboard updated!", show_alert=False)
    if isinstance(callback.message, types.Message):
        try:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass  # Message content identical


@router.callback_query(F.data == "stats:back")
async def callback_stats_back(callback: types.CallbackQuery):
    await callback_refresh_list(callback)


@router.callback_query(F.data.startswith("stats:view:"))
async def callback_stats_view(callback: types.CallbackQuery):
    if not callback.data:
        return
    chat_id = str(callback.from_user.id)
    email_id = int(callback.data.split(":")[-1])

    async with get_email_repo() as repo:
        email = await repo.get_by_id(email_id)

    if not email or not email.id or email.telegram_chat_id != chat_id:
        await callback.answer("⚠️ Email not found or access denied.", show_alert=True)
        return

    await callback.answer()
    text = _format_detail_text(email)
    kb = email_detail_keyboard(email.id)
    if isinstance(callback.message, types.Message):
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("stats:refresh:"))
async def callback_stats_refresh(callback: types.CallbackQuery):
    if not callback.data:
        return
    chat_id = str(callback.from_user.id)
    email_id = int(callback.data.split(":")[-1])

    async with get_email_repo() as repo:
        email = await repo.get_by_id(email_id)

    if not email or not email.id or email.telegram_chat_id != chat_id:
        await callback.answer("⚠️ Email not found.", show_alert=True)
        return

    await callback.answer("✅ Telemetry refreshed!", show_alert=False)
    text = _format_detail_text(email)
    kb = email_detail_keyboard(email.id)
    if isinstance(callback.message, types.Message):
        try:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass


@router.callback_query(F.data.startswith("stats:delete:"))
async def callback_stats_delete_prompt(callback: types.CallbackQuery):
    if not callback.data:
        return
    email_id = int(callback.data.split(":")[-1])
    await callback.answer()
    if isinstance(callback.message, types.Message):
        prompt_text = (
            "⚠️ <b>Delete Confirmation</b>\n\n"
            "Are you sure you want to delete this tracked email and its history?"
        )
        await callback.message.edit_text(
            prompt_text,
            parse_mode="HTML",
            reply_markup=delete_confirm_keyboard(email_id),
        )


@router.callback_query(F.data.startswith("stats:confirm_delete:"))
async def callback_stats_confirm_delete(callback: types.CallbackQuery):
    if not callback.data:
        return
    email_id = int(callback.data.split(":")[-1])
    async with get_delete_email_use_case() as use_case:
        await use_case.execute(email_id)

    await callback.answer("🗑️ Tracked email deleted.", show_alert=True)
    await callback_refresh_list(callback)
