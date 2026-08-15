import jinja2

from .tags import generate_tracking_tags, wrap_link_for_tracking
from .templates import GENERAL_EMAIL_TEMPLATE
from .types import EmailLink, EmailPayload


def format_email(payload: EmailPayload, token: str, base_url: str) -> str:
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
    return template.render(payload=formatted_payload, tracking_tags=tracking_tags)
