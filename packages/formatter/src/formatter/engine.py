import html

import jinja2

from .tags import (
    generate_tracking_tags,
    wrap_link_cloaked,
    wrap_link_for_tracking,
)
from .templates import GENERAL_EMAIL_TEMPLATE
from .types import EmailLink, EmailPayload


def detect_text_direction(text: str) -> tuple[str, str]:
    """Analyze unicode code points to determine script direction ('rtl' vs 'ltr')
    and primary language code ('ar', 'he', 'fa', 'en').
    """
    if not text:
        return "ltr", "en"

    arabic_count = sum(
        1
        for c in text
        if "\u0600" <= c <= "\u06ff"
        or "\u0750" <= c <= "\u077f"
        or "\u08a0" <= c <= "\u08ff"
        or "\ufb50" <= c <= "\ufdff"
        or "\ufe70" <= c <= "\ufeff"
    )
    hebrew_count = sum(1 for c in text if "\u0590" <= c <= "\u05ff" or "\ufb1d" <= c <= "\ufb4f")
    persian_count = sum(1 for c in text if c in ("پ", "چ", "ژ", "گ", "ی", "ک"))

    rtl_total = arabic_count + hebrew_count
    latin_count = sum(1 for c in text if ("A" <= c <= "Z") or ("a" <= c <= "z"))

    if rtl_total > 0 and rtl_total >= latin_count:
        if hebrew_count > arabic_count:
            return "rtl", "he"
        elif persian_count > 2:
            return "rtl", "fa"
        else:
            return "rtl", "ar"

    return "ltr", "en"


def format_email(payload: EmailPayload, token: str, base_url: str) -> str:
    combined_text = f"{payload.title} {payload.body_text} {payload.recipient_name or ''}"
    direction, lang_code = detect_text_direction(combined_text)
    text_align = "right" if direction == "rtl" else "left"

    tracking_tags = generate_tracking_tags(token, base_url)
    tracked_links = [
        EmailLink(text=link.text, url=wrap_link_for_tracking(link.url, token, base_url))
        for link in payload.links
    ]
    formatted_payload = EmailPayload(
        title=payload.title,
        body_text=payload.body_text,
        recipient_name=payload.recipient_name,
        sender_name=payload.sender_name,
        links=tracked_links,
    )
    template = jinja2.Template(GENERAL_EMAIL_TEMPLATE)
    return template.render(
        payload=formatted_payload,
        tracking_tags=tracking_tags,
        direction=direction,
        lang_code=lang_code,
        text_align=text_align,
    )


def generate_plaintext_mirror(html_content: str) -> str:
    """Generate a clean, synchronized RFC 2046 text/plain alternative body from HTML content
    to satisfy SpamAssassin and avoid MIME_HTML_ONLY penalties.
    """
    import html
    import re

    # Remove style and script tags
    text = re.sub(
        r"<(style|script)[^>]*>.*?</\1>", "", html_content, flags=re.DOTALL | re.IGNORECASE
    )
    # Convert links <a href="url">text</a> to text [url]
    text = re.sub(
        r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        r"\2 [\1]",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # Convert breaks and block elements to newlines
    text = re.sub(r"<(br|p|div|tr|h[1-6])[^>]*>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Unescape HTML entities
    text = html.unescape(text)
    # Normalize whitespace
    lines = [line.strip() for line in text.splitlines()]
    clean_text = "\n".join(line for line in lines if line)
    return clean_text


def generate_document_preview_card(
    filename: str,
    target_url: str,
    token: str,
    base_url: str,
    filesize: str = "1.2 MB",
) -> str:
    """Generate an interactive document preview card wrapped with cloaked tracking."""
    cloaked_link = wrap_link_cloaked(target_url, token, base_url)
    ext = filename.rsplit(".", 1)[-1].upper() if "." in filename else "DOC"
    return (
        '<table role="presentation" border="0" cellpadding="0" cellspacing="0" '
        'style="margin:16px 0;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
        'padding:12px;width:100%;max-width:480px;">\n'
        "  <tr>\n"
        '    <td style="width:40px;text-align:center;font-size:24px;">📄</td>\n'
        '    <td style="padding-left:12px;">\n'
        f'      <div style="font-size:14px;font-weight:600;color:#1e293b;">{filename}</div>\n'
        f'      <div style="font-size:12px;color:#64748b;">{ext} Document • {filesize}</div>\n'
        "    </td>\n"
        '    <td style="text-align:right;">\n'
        f'      <a href="{cloaked_link}" style="display:inline-block;padding:6px 14px;'
        "background:#2563eb;color:#ffffff;text-decoration:none;font-size:12px;font-weight:600;"
        'border-radius:6px;">View</a>\n'
        "    </td>\n"
        "  </tr>\n"
        "</table>"
    )


def generate_bimi_svg_ps(
    title: str,
    initials: str = "MB",
    bg_color: str = "#2563eb",
) -> str:
    """Generate a valid SVG Tiny 1.2 Portable/Secure (Tiny P/S) compliant brand avatar
    for Google Workspace & Yahoo Mail BIMI / VMC verified sender certification.
    """
    clean_title = html.escape(title)
    clean_init = html.escape(initials[:3].upper())
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg version="1.2" baseProfile="tiny-ps" xmlns="http://www.w3.org/2000/svg" '
        'width="100%" height="100%" viewBox="0 0 100 100">\n'
        f"  <title>{clean_title}</title>\n"
        f'  <circle cx="50" cy="50" r="48" fill="{bg_color}" />\n'
        '  <text x="50" y="58" font-size="32" font-weight="bold" fill="#ffffff" '
        f'text-anchor="middle" font-family="sans-serif">{clean_init}</text>\n'
        "</svg>"
    )
