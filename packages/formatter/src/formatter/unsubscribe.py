from typing import Dict, Optional


def generate_unsubscribe_headers(
    token: str,
    base_url: str,
    mailto: Optional[str] = None,
) -> Dict[str, str]:
    """Generate RFC 2369 and RFC 8058 compliant email headers required by
    Google, Yahoo, and Microsoft for inbox deliverability compliance.
    """
    clean_base = base_url.rstrip("/")
    unsub_url = f"{clean_base}/unsub/{token}"
    domain = clean_base.split("://", 1)[-1].split("/")[0].split(":")[0]

    if mailto:
        unsub_target = f"<{unsub_url}>, <mailto:{mailto}?subject=unsubscribe-{token}>"
    else:
        unsub_target = f"<{unsub_url}>"

    return {
        "List-Unsubscribe": unsub_target,
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        "List-Id": f"<mailblinker-{token[:8]}.{domain}>",
    }
