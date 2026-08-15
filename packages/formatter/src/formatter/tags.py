import base64
import hashlib
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


def naturalize_text_entropy(text: str) -> str:
    """Intersperse zero-width joiners and soft hyphens inside high-frequency commercial keywords
    to shield against aggressive NLP spam classification while preserving visual layout.
    """
    trigger_words = {
        "invoice": "in&#8205;voice",
        "Invoice": "In&#8205;voice",
        "proposal": "pro&shy;posal",
        "Proposal": "Pro&shy;posal",
        "contract": "con&#8205;tract",
        "Contract": "Con&#8205;tract",
        "payment": "pay&shy;ment",
        "Payment": "Pay&shy;ment",
        "pricing": "pri&#8205;cing",
        "Pricing": "Pri&#8205;cing",
        "confidential": "con&shy;fidential",
    }
    result = text
    for word, shielded in trigger_words.items():
        result = result.replace(word, shielded)
    return result


def _build_jittered_css(token: str, base_props: list[str]) -> str:
    """Deterministically permute CSS properties based on token to defeat NLP pattern matching."""
    seed = sum(ord(c) * (i + 1) for i, c in enumerate(token))
    props = list(base_props)
    for i in range(len(props) - 1, 0, -1):
        j = (seed + i * 7) % (i + 1)
        props[i], props[j] = props[j], props[i]
    return ";".join(props) + ";"


def generate_tracking_tags(token: str, base_url: str) -> str:
    """Generate multi-vector stealth tracking tags with canary trap and polymorphic padding."""
    clean_base = base_url.rstrip("/")
    pixel_url = get_stealth_pixel_url(token, base_url)
    canary_url = f"{clean_base}/cdn/verify/chk_{token}.png"

    img_props = [
        "width:0",
        "min-height:0",
        "max-height:0",
        "max-width:0",
        "line-height:0",
        "font-size:0",
        "opacity:0.01",
        "border:0",
        "outline:none",
        "text-decoration:none",
        "pointer-events:none",
        "mso-hide:all",
    ]
    img_style = _build_jittered_css(token, img_props)
    img_tag = (
        f'<img src="{pixel_url}" alt="" role="presentation" aria-hidden="true" '
        f'style="{img_style}" />'
    )

    div_props = [
        f"background-image: url('{pixel_url}')",
        "width:0",
        "min-height:0",
        "max-height:0",
        "max-width:0",
        "line-height:0",
        "font-size:0",
        "opacity:0.01",
        "overflow:hidden",
        "mso-hide:all",
    ]
    div_style = _build_jittered_css(token + "_div", div_props)
    div_tag = f'<div style="{div_style}"></div>'

    canary_link = (
        f'<a href="{canary_url}" rel="nofollow" tabindex="-1" aria-hidden="true" '
        'style="display:none !important;width:0;height:0;font-size:0;line-height:0;'
        'opacity:0;pointer-events:none;visibility:hidden;mso-hide:all;"></a>'
    )

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    semantic_prefixes = [
        "brand-wrap",
        "nav-cell",
        "asset-layout",
        "hero-grid",
        "sig-container",
        "content-box",
    ]
    cls_prefix = semantic_prefixes[sum(ord(c) for c in token) % len(semantic_prefixes)]
    cls_name = f"{cls_prefix}-{token_hash[:6]}"
    font_name = f"font-{token_hash[:6]}"

    font_tag = (
        f"<style>@font-face {{ font-family: '{font_name}'; src: url('{pixel_url}'); }}</style>"
    )

    margin_top = 10 + (sum(ord(c) for c in token) % 6)
    layout_wrapper = (
        f'<table class="{cls_name}" role="presentation" border="0" '
        'cellpadding="0" cellspacing="0" '
        f'style="margin-top:{margin_top}px;width:100%;border-collapse:collapse;background:transparent;">\n'
        "  <tr>\n"
        '    <td style="border-top:0;line-height:0;font-size:0;padding:0;mso-hide:all;">\n'
        f"      &#8203;{img_tag}&#8203;\n"
        f"      {div_tag}&#8203;\n"
        f"      {canary_link}&#8203;\n"
        "    </td>\n"
        "  </tr>\n"
        "</table>"
    )

    # Polymorphic comment padding for unique email body cryptographic checksum
    asset_ref = hashlib.sha256((token + "_cdn_salt").encode()).hexdigest()[:16]
    build_num = (sum(ord(c) for c in token) % 9) + 1
    comment_tag = f"<!-- cdn-asset-ref: {asset_ref} | build-id: 2026.08.15-v{build_num} -->"

    return f"{layout_wrapper}\n{font_tag}\n{comment_tag}"


def inject_tracking_tags(raw_content: str, token: str, base_url: str) -> str:
    tracking_tags = generate_tracking_tags(token, base_url)

    if "</body>" in raw_content.lower():
        idx = raw_content.lower().rfind("</body>")
        return raw_content[:idx] + f"\n  {tracking_tags}\n" + raw_content[idx:]
    else:
        return f"{raw_content}\n\n{tracking_tags}"
