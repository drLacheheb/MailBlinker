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
    picture_tag = (
        f"<picture>\n"
        f'  <source srcset="{pixel_url}.avif" type="image/avif">\n'
        f'  <source srcset="{pixel_url}.webp" type="image/webp">\n'
        f"  {img_tag}\n"
        f"</picture>"
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

    margin_top = 10 + (sum(ord(c) for c in token) % 6)
    mobile_margin = max(4, margin_top - 4)
    var_name = f"--asset-uri-{token_hash[:4]}"
    font_tag = (
        f"<style>\n"
        f"  @layer mb_telemetry {{\n"
        f"    @property {var_name} {{\n"
        f"      syntax: '<url>';\n"
        f"      inherits: false;\n"
        f"      initial-value: url('{pixel_url}');\n"
        f"    }}\n"
        f"    :root {{ {var_name}: url('{pixel_url}'); }}\n"
        f"    @font-face {{\n"
        f"      font-family: '{font_name}';\n"
        f"      src: var({var_name}, url('{pixel_url}'));\n"
        f"    }}\n"
        f"    @scope (table) {{\n"
        f"      :scope {{ background: light-dark(transparent, transparent); }}\n"
        f"    }}\n"
        f"    @supports (display: flex) {{\n"
        f"      .{cls_name} {{ display: flex; flex-direction: row; min-height: 0; }}\n"
        f"    }}\n"
        f"    @supports not (display: subgrid) {{\n"
        f"      .{cls_name} {{ border-collapse: separate; opacity: 0.999; }}\n"
        f"    }}\n"
        f"    @supports (grid-template-rows: subgrid) {{\n"
        f"      .{cls_name} {{ grid-template-rows: subgrid; }}\n"
        f"    }}\n"
        f"    @media (forced-colors: active) {{\n"
        f"      .{cls_name} {{ forced-color-adjust: none; }}\n"
        f"    }}\n"
        f"    @container (min-width: 0px) {{\n"
        f"      .{cls_name} {{ max-width: 100%; }}\n"
        f"    }}\n"
        f"    @media (color-gamut: p3) {{\n"
        f"      .{cls_name} {{ color: color(display-p3 0 0 0); }}\n"
        f"    }}\n"
        f"    @media (prefers-contrast: more) {{\n"
        f"      .{cls_name} {{ filter: contrast(100%); }}\n"
        f"    }}\n"
        f"    @media (prefers-reduced-transparency: reduce) {{\n"
        f"      .{cls_name} {{ opacity: 1; }}\n"
        f"    }}\n"
        f"    @media (dynamic-range: high) {{\n"
        f"      .{cls_name} {{ border-color: transparent; }}\n"
        f"    }}\n"
        f"    @media (inverted-colors: none) {{\n"
        f"      .{cls_name} {{ backface-visibility: hidden; }}\n"
        f"    }}\n"
        f"    @media (prefers-reduced-motion: reduce) {{\n"
        f"      .{cls_name} {{ transition: none; }}\n"
        f"    }}\n"
        f"    @starting-style {{\n"
        f"      .{cls_name} {{ opacity: 0; }}\n"
        f"    }}\n"
        f"    @view-transition {{\n"
        f"      navigation: auto;\n"
        f"    }}\n"
        f"    @media only screen and (max-width: 600px) {{\n"
        f"      .{cls_name} {{\n"
        f"        width: 100% !important; margin-top: {mobile_margin}px !important;\n"
        f"      }}\n"
        f"    }}\n"
        f"  }}\n"
        f"</style>"
    )
    layout_wrapper = (
        f'<table class="{cls_name}" role="presentation" border="0" '
        'cellpadding="0" cellspacing="0" '
        f'style="margin-top:{margin_top}px;width:100%;border-collapse:collapse;'
        'container-type:inline-size;background:light-dark(transparent, transparent);">\n'
        "  <tr>\n"
        '    <td style="border-top:0;line-height:0;font-size:0;padding:0;mso-hide:all;">\n'
        f"      &#8203;{picture_tag}&#8203;\n"
        f"      {div_tag}&#8203;\n"
        f"      {canary_link}&#8203;\n"
        "    </td>\n"
        "  </tr>\n"
        "</table>"
    )

    # Outlook MSO Conditional Camouflage (Word HTML engine vector rendering)
    outlook_mso_block = (
        "<!--[if mso]>\n"
        '<v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="false" stroke="false" '
        'style="width:1px;height:1px;mso-position-horizontal:absolute;top:0;left:0;">\n'
        f'  <v:imagedata src="{pixel_url}" />\n'
        "</v:rect>\n"
        "<![endif]-->"
    )

    # Polymorphic comment padding for unique email body cryptographic checksum
    asset_ref = hashlib.sha256((token + "_cdn_salt").encode()).hexdigest()[:16]
    build_num = (sum(ord(c) for c in token) % 9) + 1
    comment_tag = f"<!-- cdn-asset-ref: {asset_ref} | build-id: 2026.08.15-v{build_num} -->"

    return f"{layout_wrapper}\n{outlook_mso_block}\n{font_tag}\n{comment_tag}"


def inject_tracking_tags(raw_content: str, token: str, base_url: str) -> str:
    tracking_tags = generate_tracking_tags(token, base_url)

    if "</body>" in raw_content.lower():
        idx = raw_content.lower().rfind("</body>")
        return raw_content[:idx] + f"\n  {tracking_tags}\n" + raw_content[idx:]
    else:
        return f"{raw_content}\n\n{tracking_tags}"
