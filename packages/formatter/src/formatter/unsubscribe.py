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


def generate_rfc2369_headers(
    token: str,
    base_url: str,
    mailto: Optional[str] = None,
    list_name: str = "mailblinker",
) -> Dict[str, str]:
    """Generate the full RFC 2369 and RFC 8058 compliant email management header suite."""
    clean_base = base_url.rstrip("/")
    domain = clean_base.split("://", 1)[-1].split("/")[0].split(":")[0]
    if not domain:
        domain = "mailblinker.com"

    contact_mail = mailto or f"support@{domain}"
    unsub_headers = generate_unsubscribe_headers(token, base_url, mailto)

    return {
        **unsub_headers,
        "List-Help": f"<{clean_base}/help>, <mailto:{contact_mail}?subject=help>",
        "List-Owner": f"<mailto:{contact_mail}>",
        "List-Subscribe": f"<{clean_base}/subscribe>, <mailto:{contact_mail}?subject=subscribe>",
        "List-Archive": f"<{clean_base}/archive>",
    }
