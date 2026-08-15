from .density import DensityReport, EmailDensityOptimizer
from .engine import format_email, generate_document_preview_card
from .mime import generate_mime_boundary
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

__all__ = [
    "EmailPayload",
    "EmailLink",
    "EmailDensityOptimizer",
    "DensityReport",
    "generate_mime_boundary",
    "naturalize_text_entropy",
    "format_email",
    "generate_document_preview_card",
    "generate_tracking_tags",
    "inject_tracking_tags",
    "get_stealth_pixel_url",
    "wrap_link_for_tracking",
    "wrap_link_cloaked",
    "CAMOUFLAGE_PATTERNS",
]
