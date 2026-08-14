def generate_tracking_tags(token: str, base_url: str) -> str:
    clean_base = base_url.rstrip("/")
    pixel_url = f"{clean_base}/track/{token}.gif"

    img_tag = (
        f'<img src="{pixel_url}" width="1" height="1" alt="" '
        'style="display:none !important; width:0px; height:0px; '
        "max-height:0px; max-width:0px; opacity:0; overflow:hidden; "
        'mso-hide:all; font-size:0px; line-height:0px;" />'
    )
    div_tag = (
        f"<div style=\"background-image: url('{pixel_url}'); "
        "display:none !important; mso-hide:all; width:0px; height:0px; "
        'max-height:0px; overflow:hidden;"></div>'
    )

    return f"{img_tag}\n{div_tag}"


def inject_tracking_tags(raw_content: str, token: str, base_url: str) -> str:
    tracking_tags = generate_tracking_tags(token, base_url)

    if "</body>" in raw_content.lower():
        idx = raw_content.lower().rfind("</body>")
        return raw_content[:idx] + f"\n  {tracking_tags}\n" + raw_content[idx:]
    else:
        return f"{raw_content}\n\n{tracking_tags}"
