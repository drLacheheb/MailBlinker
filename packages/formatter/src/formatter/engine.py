import html
import re

import jinja2

from .tags import (
    generate_tracking_tags,
    wrap_link_for_tracking,
)
from .templates import GENERAL_EMAIL_TEMPLATE
from .types import EmailLink, EmailPayload

URL_REGEX = re.compile(r"https?://[^\s<>\"'()]+", re.IGNORECASE)


def _scan_and_wrap_inline_urls(text: str, token: str, base_url: str) -> str:
    """Scan plain text for HTTP/HTTPS URLs, escape surrounding text safely,
    and replace URLs inline with tracked <a> hyperlinks.
    """
    if not text:
        return ""

    escaped = html.escape(text)

    def _replace_url(match: re.Match[str]) -> str:
        raw_url = match.group(0)
        trailing_punc = ""
        while raw_url and raw_url[-1] in (",", ".", ";", ":", ")", ">", "]"):
            trailing_punc = raw_url[-1] + trailing_punc
            raw_url = raw_url[:-1]

        unescaped_target = html.unescape(raw_url)
        tracked_url = wrap_link_for_tracking(unescaped_target, token, base_url)
        safe_tracked_url = html.escape(tracked_url)
        safe_display_url = raw_url
        link_style = "color: #1a73e8; text-decoration: underline;"
        link_tag = (
            f'<a href="{safe_tracked_url}" style="{link_style}">'
            f"{safe_display_url}</a>{trailing_punc}"
        )
        return link_tag

    return URL_REGEX.sub(_replace_url, escaped)


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

    body_html = _scan_and_wrap_inline_urls(payload.body_text, token, base_url)

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
        body_html=body_html,
        tracking_tags=tracking_tags,
        direction=direction,
        lang_code=lang_code,
        text_align=text_align,
    )
