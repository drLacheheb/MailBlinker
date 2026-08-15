from typing import List, Optional

from aiogram.types import (
    CopyTextButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from core import TrackedEmailEntity


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Persistent 2x2 reply keyboard for quick, click-first navigation."""
    keyboard = [
        [
            KeyboardButton(text="⚡ Fast Track"),
            KeyboardButton(text="📝 Compose Email"),
        ],
        [
            KeyboardButton(text="📊 My Analytics"),
            KeyboardButton(text="❓ How to Use"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


def email_created_inline_keyboard(
    pixel_url: str, email_id: Optional[int] = None
) -> InlineKeyboardMarkup:
    """Action buttons attached to freshly created email cards."""
    buttons: List[List[InlineKeyboardButton]] = []

    # 1-Tap Copy Button (Native Telegram Bot API feature)
    try:
        copy_btn = InlineKeyboardButton(
            text="📋 Copy Tracking Pixel URL",
            copy_text=CopyTextButton(text=pixel_url),
        )
        buttons.append([copy_btn])
    except Exception:
        # Fallback if client doesn't support copy_text
        pass

    action_row = []
    if email_id:
        action_row.append(
            InlineKeyboardButton(text="📊 View Stats", callback_data=f"stats:view:{email_id}")
        )
    action_row.append(
        InlineKeyboardButton(text="➕ Track Another", callback_data="action:fast_track")
    )
    buttons.append(action_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def wizard_step_keyboard(can_skip: bool = False) -> InlineKeyboardMarkup:
    """Navigation buttons for wizard steps."""
    row: List[InlineKeyboardButton] = []
    if can_skip:
        row.append(InlineKeyboardButton(text="⏭️ Skip Step", callback_data="wizard:skip"))
    row.append(InlineKeyboardButton(text="❌ Cancel", callback_data="wizard:cancel"))
    return InlineKeyboardMarkup(inline_keyboard=[row])


def stats_list_keyboard(emails: List[TrackedEmailEntity]) -> InlineKeyboardMarkup:
    """List of tracked emails rendered as interactive buttons."""
    buttons: List[List[InlineKeyboardButton]] = []

    for e in emails[:8]:  # Show top 8 recent emails
        status_icon = "🟢" if e.open_count > 0 else "⏳"
        count_text = f" ({e.open_count}x)" if e.open_count > 0 else ""
        btn_text = f"{status_icon} {e.title[:22]}{count_text}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"stats:view:{e.id}")])

    buttons.append(
        [
            InlineKeyboardButton(text="🔄 Refresh Dashboard", callback_data="stats:refresh_list"),
            InlineKeyboardButton(text="➕ New Tracker", callback_data="action:fast_track"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def email_detail_keyboard(email_id: int) -> InlineKeyboardMarkup:
    """Action controls when viewing a specific email's telemetry."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Live Refresh", callback_data=f"stats:refresh:{email_id}"
                ),
                InlineKeyboardButton(text="🗑️ Delete", callback_data=f"stats:delete:{email_id}"),
            ],
            [
                InlineKeyboardButton(text="🔙 Back to My Emails", callback_data="stats:back"),
            ],
        ]
    )


def delete_confirm_keyboard(email_id: int) -> InlineKeyboardMarkup:
    """Confirmation buttons before deleting an email."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚠️ Yes, Delete", callback_data=f"stats:confirm_delete:{email_id}"
                ),
                InlineKeyboardButton(text="❌ Cancel", callback_data=f"stats:view:{email_id}"),
            ]
        ]
    )
