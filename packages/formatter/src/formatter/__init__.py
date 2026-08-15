from .density import DensityReport, EmailDensityOptimizer
from .engine import (
    format_email,
    generate_document_preview_card,
    generate_plaintext_mirror,
)
from .mime import (
    encode_mime_body,
    generate_enterprise_message_id,
    generate_feedback_id_headers,
    generate_mime_boundary,
    generate_rfc2822_date,
)
from .tags import (
    CAMOUFLAGE_PATTERNS,
    generate_tracking_tags,
    get_stealth_pixel_url,
    inject_tracking_tags,
    naturalize_text_entropy,
    wrap_link_cloaked,
    wrap_link_for_tracking,
)
from .types import EmailLink, EmailPayload
from .unsubscribe import generate_unsubscribe_headers

__all__ = [
    "EmailPayload",
    "EmailLink",
    "EmailDensityOptimizer",
    "DensityReport",
    "generate_mime_boundary",
    "encode_mime_body",
    "generate_enterprise_message_id",
    "generate_rfc2822_date",
    "generate_feedback_id_headers",
    "naturalize_text_entropy",
    "generate_unsubscribe_headers",
    "format_email",
    "generate_plaintext_mirror",
    "generate_document_preview_card",
    "generate_tracking_tags",
    "inject_tracking_tags",
    "get_stealth_pixel_url",
    "wrap_link_for_tracking",
    "wrap_link_cloaked",
    "CAMOUFLAGE_PATTERNS",
]
