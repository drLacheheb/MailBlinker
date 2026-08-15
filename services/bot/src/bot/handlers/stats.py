import html
from typing import Optional

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..dependencies import (
    get_delete_email_use_case,
    get_email_repo,
    get_list_emails_use_case,
    get_update_notify_settings_use_case,
)
from ..keyboards import (
    delete_confirm_keyboard,
    email_detail_keyboard,
    main_menu_keyboard,
    notify_settings_keyboard,
    stats_list_keyboard,
    wizard_step_keyboard,
)

router = Router()


class CustomLimitState(StatesGroup):
    waiting_for_number = State()


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

    if email.notify_limit == 0:
        alert_info = "🔕 Muted"
    elif email.notify_limit is None:
        alert_info = "🔔 Unlimited"
    elif email.notify_limit == 1:
        alert_info = "🔔 1st Only"
    else:
        alert_info = f"🔔 Max {email.notify_limit}x"

    fwd_info = " • 🔀 Fwd: ON" if email.notify_forwarding else " • 🔀 Fwd: OFF"

    lines = [
        f"{status_icon} <b>{safe_title}</b>",
        f"👤 <code>{safe_recipient}</code> • {status_text}",
        f"⚙️ <b>Alerts:</b> {alert_info}{fwd_info}",
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
    kb = email_detail_keyboard(
        email.id, notify_limit=email.notify_limit, notify_forwarding=email.notify_forwarding
    )
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
    kb = email_detail_keyboard(
        email.id, notify_limit=email.notify_limit, notify_forwarding=email.notify_forwarding
    )
    if isinstance(callback.message, types.Message):
        try:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass


@router.callback_query(F.data.startswith("stats:quick_mute:"))
async def callback_stats_quick_mute(callback: types.CallbackQuery):
    if not callback.data:
        return
    chat_id = str(callback.from_user.id)
    email_id = int(callback.data.split(":")[-1])

    async with get_email_repo() as repo:
        email = await repo.get_by_id(email_id)

    if not email or not email.id or email.telegram_chat_id != chat_id:
        await callback.answer("⚠️ Email not found or access denied.", show_alert=True)
        return

    async with get_update_notify_settings_use_case() as use_case:
        await use_case.execute(email_id=email_id, limit=0, update_limit=True)

    await callback.answer("🔕 Future alerts muted for this email!", show_alert=True)


@router.callback_query(F.data.startswith("stats:settings_menu:"))
async def callback_stats_settings_menu(callback: types.CallbackQuery):
    if not callback.data:
        return
    chat_id = str(callback.from_user.id)
    email_id = int(callback.data.split(":")[-1])

    async with get_email_repo() as repo:
        email = await repo.get_by_id(email_id)

    if not email or not email.id or email.telegram_chat_id != chat_id:
        await callback.answer("⚠️ Email not found.", show_alert=True)
        return

    await callback.answer()
    text = (
        f"⚙️ <b>Notification Settings</b>\n"
        f"📧 <b>{html.escape(email.title)}</b>\n\n"
        f"Set max notification limit or toggle smart forwarding alerts:"
    )
    kb = notify_settings_keyboard(
        email_id=email.id,
        current_limit=email.notify_limit,
        notify_forwarding=email.notify_forwarding,
    )
    if isinstance(callback.message, types.Message):
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("stats:set_limit:"))
async def callback_stats_set_limit(callback: types.CallbackQuery):
    if not callback.data:
        return
    chat_id = str(callback.from_user.id)
    parts = callback.data.split(":")
    email_id = int(parts[2])
    raw_val = parts[3]

    new_limit: Optional[int] = None if raw_val == "none" else int(raw_val)

    async with get_email_repo() as repo:
        email = await repo.get_by_id(email_id)

    if not email or not email.id or email.telegram_chat_id != chat_id:
        await callback.answer("⚠️ Access denied.", show_alert=True)
        return

    async with get_update_notify_settings_use_case() as use_case:
        updated = await use_case.execute(email_id=email_id, limit=new_limit, update_limit=True)

    if not updated or not updated.id:
        await callback.answer("⚠️ Error updating settings.", show_alert=True)
        return

    msg = (
        "✅ Alerts set to Unlimited" if new_limit is None else f"✅ Alert limit set to {new_limit}"
    )
    if new_limit == 0:
        msg = "🔕 Alerts muted for this email"
    await callback.answer(msg, show_alert=False)

    text = (
        f"⚙️ <b>Notification Settings</b>\n"
        f"📧 <b>{html.escape(updated.title)}</b>\n\n"
        f"Set max notification limit or toggle smart forwarding alerts:"
    )
    kb = notify_settings_keyboard(
        email_id=updated.id,
        current_limit=updated.notify_limit,
        notify_forwarding=updated.notify_forwarding,
    )
    if isinstance(callback.message, types.Message):
        try:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass


@router.callback_query(F.data.startswith("stats:toggle_forwarding:"))
async def callback_stats_toggle_forwarding(callback: types.CallbackQuery):
    if not callback.data:
        return
    chat_id = str(callback.from_user.id)
    email_id = int(callback.data.split(":")[-1])

    async with get_email_repo() as repo:
        email = await repo.get_by_id(email_id)

    if not email or not email.id or email.telegram_chat_id != chat_id:
        await callback.answer("⚠️ Access denied.", show_alert=True)
        return

    new_fwd = not email.notify_forwarding
    async with get_update_notify_settings_use_case() as use_case:
        updated = await use_case.execute(email_id=email_id, notify_forwarding=new_fwd)

    if not updated or not updated.id:
        await callback.answer("⚠️ Error updating settings.", show_alert=True)
        return

    status_msg = "🔀 Forwarding alerts ON" if new_fwd else "🔀 Forwarding alerts OFF"
    await callback.answer(f"✅ {status_msg}", show_alert=False)

    text = (
        f"⚙️ <b>Notification Settings</b>\n"
        f"📧 <b>{html.escape(updated.title)}</b>\n\n"
        f"Set max notification limit or toggle smart forwarding alerts:"
    )
    kb = notify_settings_keyboard(
        email_id=updated.id,
        current_limit=updated.notify_limit,
        notify_forwarding=updated.notify_forwarding,
    )
    if isinstance(callback.message, types.Message):
        try:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass


@router.callback_query(F.data.startswith("stats:custom_limit:"))
async def callback_stats_custom_limit(callback: types.CallbackQuery, state: FSMContext):
    if not callback.data:
        return
    email_id = int(callback.data.split(":")[-1])
    await state.update_data(email_id=email_id)
    await state.set_state(CustomLimitState.waiting_for_number)
    await callback.answer()

    prompt = (
        "✏️ <b>Custom Alert Limit</b>\n\n"
        "Send max notifications for this email (e.g. <code>5</code>):"
    )
    if isinstance(callback.message, types.Message):
        await callback.message.answer(
            prompt, parse_mode="HTML", reply_markup=wizard_step_keyboard(can_skip=False)
        )


@router.message(CustomLimitState.waiting_for_number)
async def process_custom_limit(message: types.Message, state: FSMContext):
    raw_text = (message.text or "").strip()
    try:
        val = int(raw_text)
        if val < 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "⚠️ Please send a valid positive number (e.g. <code>5</code>):", parse_mode="HTML"
        )
        return

    data = await state.get_data()
    email_id = data.get("email_id")
    await state.clear()

    if not email_id:
        await message.answer("⚠️ Session expired.", reply_markup=main_menu_keyboard())
        return

    async with get_update_notify_settings_use_case() as use_case:
        updated = await use_case.execute(email_id=email_id, limit=val, update_limit=True)

    if not updated or not updated.id:
        await message.answer("⚠️ Email not found.", reply_markup=main_menu_keyboard())
        return

    text = _format_detail_text(updated)
    kb = email_detail_keyboard(
        updated.id, notify_limit=updated.notify_limit, notify_forwarding=updated.notify_forwarding
    )
    await message.answer(
        f"✅ <b>Alert limit set to {val}!</b>\n\n{text}",
        parse_mode="HTML",
        reply_markup=kb,
    )


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
