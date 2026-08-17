import base64
import json
import urllib.parse

CAMOUFLAGE_PATTERNS = [
    "assets/signature/sig_{token}.png?v=1.2",
    "cdn/media/logo_{token}.png?res=2x",
    "static/images/badge_{token}.png?fmt=png",
    "assets/img/spacer_{token}.png?w=120",
    "static/branding/brand_{token}.png?v=2.0",
    "cdn/assets/icon_{token}.png?res=hd",
    "assets/media/photo_{token}.png?q=90",
    "cdn/fonts/glyph_{token}.png?v=1.0",
    "cdn/graphics/vector_{token}.svg?v=1.0",
]


def get_stealth_pixel_url(token: str, base_url: str) -> str:
    """Generate a realistic semantic asset URL from the camouflage pool with version salt."""
    clean_base = base_url.rstrip("/")
    idx = sum(ord(c) for c in token) % len(CAMOUFLAGE_PATTERNS)
    pattern = CAMOUFLAGE_PATTERNS[idx]
    relative_path = pattern.format(token=token)
    return f"{clean_base}/{relative_path}"


def wrap_link_for_tracking(target_url: str, token: str, base_url: str) -> str:
    """Wrap an outbound hyperlink for semantic click-through tracking."""
    clean_base = base_url.rstrip("/")
    encoded_dest = urllib.parse.quote(target_url, safe="")
    return f"{clean_base}/l/{token}?dest={encoded_dest}"


def wrap_link_cloaked(target_url: str, token: str, base_url: str) -> str:
    """Wrap an outbound hyperlink with compact Base64URL payload obfuscation."""
    clean_base = base_url.rstrip("/")
    payload_json = json.dumps({"t": token, "u": target_url}, separators=(",", ":"))
    encoded = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("ascii").rstrip("=")
    return f"{clean_base}/cdn/go/{encoded}"


def generate_tracking_tags(token: str, base_url: str) -> str:
    """Generate an invisible, industry-standard 1x1 image tracking pixel.
    Completely innocent to spam filters and auto-rendered by email clients.
    """
    pixel_url = get_stealth_pixel_url(token, base_url)
    return (
        f'<img src="{pixel_url}" width="1" height="1" border="0" alt="" '
        'style="width: 1px !important; height: 1px !important; border: 0 !important; '
        "margin: 0 !important; padding: 0 !important; outline: none !important; "
        'min-height: 1px !important; max-height: 1px !important;" />'
    )


def inject_tracking_tags(raw_content: str, token: str, base_url: str) -> str:
    tracking_tags = generate_tracking_tags(token, base_url)

    if "</body>" in raw_content.lower():
        idx = raw_content.lower().rfind("</body>")
        return raw_content[:idx] + f"\n  {tracking_tags}\n" + raw_content[idx:]
    else:
        return f"{raw_content}\n\n{tracking_tags}"
