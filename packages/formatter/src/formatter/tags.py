CAMOUFLAGE_PATTERNS = [
    "assets/signature/sig_{token}.png?v=1.2",
    "cdn/media/logo_{token}.png?res=2x",
    "static/images/badge_{token}.png?fmt=png",
    "assets/img/spacer_{token}.png?w=120",
    "static/branding/brand_{token}.png?v=2.0",
    "cdn/assets/icon_{token}.png?res=hd",
    "assets/media/photo_{token}.png?q=90",
    "cdn/fonts/glyph_{token}.png?v=1.0",
]


def get_stealth_pixel_url(token: str, base_url: str) -> str:
    """Generate a realistic semantic asset URL from the camouflage pool with version salt."""
    clean_base = base_url.rstrip("/")
    idx = sum(ord(c) for c in token) % len(CAMOUFLAGE_PATTERNS)
    pattern = CAMOUFLAGE_PATTERNS[idx]
    relative_path = pattern.format(token=token)
    return f"{clean_base}/{relative_path}"


def generate_tracking_tags(token: str, base_url: str) -> str:
    """Generate multi-vector stealth tracking tags embedded in a semantic presentation table."""
    pixel_url = get_stealth_pixel_url(token, base_url)

    img_tag = (
        f'<img src="{pixel_url}" alt="" role="presentation" aria-hidden="true" '
        'style="width:0;min-height:0;max-height:0;max-width:0;line-height:0;'
        "font-size:0;opacity:0.01;border:0;outline:none;text-decoration:none;"
        'pointer-events:none;mso-hide:all;" />'
    )
    div_tag = (
        f"<div style=\"background-image: url('{pixel_url}'); "
        "width:0;min-height:0;max-height:0;max-width:0;line-height:0;"
        'font-size:0;opacity:0.01;overflow:hidden;mso-hide:all;"></div>'
    )
    font_tag = f"<style>@font-face {{ font-family: 'mb-glyph'; src: url('{pixel_url}'); }}</style>"

    layout_wrapper = (
        '<table role="presentation" border="0" cellpadding="0" cellspacing="0" '
        'style="margin-top:12px;width:100%;border-collapse:collapse;">\n'
        "  <tr>\n"
        '    <td style="border-top:0;line-height:0;font-size:0;padding:0;mso-hide:all;">\n'
        f"      {img_tag}\n"
        f"      {div_tag}\n"
        "    </td>\n"
        "  </tr>\n"
        "</table>"
    )

    return f"{layout_wrapper}\n{font_tag}"


def inject_tracking_tags(raw_content: str, token: str, base_url: str) -> str:
    tracking_tags = generate_tracking_tags(token, base_url)

    if "</body>" in raw_content.lower():
        idx = raw_content.lower().rfind("</body>")
        return raw_content[:idx] + f"\n  {tracking_tags}\n" + raw_content[idx:]
    else:
        return f"{raw_content}\n\n{tracking_tags}"
