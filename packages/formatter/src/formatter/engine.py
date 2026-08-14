import jinja2

from .tags import generate_tracking_tags
from .templates import GENERAL_EMAIL_TEMPLATE
from .types import EmailPayload


def format_email(payload: EmailPayload, token: str, base_url: str) -> str:
    tracking_tags = generate_tracking_tags(token, base_url)
    template = jinja2.Template(GENERAL_EMAIL_TEMPLATE)
    return template.render(payload=payload, tracking_tags=tracking_tags)
