import random
import time
import uuid
from typing import Optional


def generate_mime_boundary(client_type: str = "auto") -> str:
    """Generate realistic client-mimicking MIME multipart boundaries to defeat
    automated mass-mailer heuristic scanners.
    """
    if client_type == "auto":
        client_type = random.choice(["apple_mail", "outlook", "thunderbird"])

    client_lower = client_type.lower()
    ts = int(time.time())

    if client_lower == "apple_mail":
        part_a = random.randint(1000, 9999)
        part_b = random.randint(100000, 999999)
        return f"----=_Part_{part_a}_{ts}.{part_b}"
    elif client_lower == "outlook":
        hex_id = uuid.uuid4().hex[:12].upper()
        return f"--_000_{hex_id}DB7PR04MB4567_"
    else:  # thunderbird
        hex_seq = uuid.uuid4().hex[:24].upper()
        return f"------------{hex_seq}"


def encode_mime_body(html_content: str, encoding: str = "auto") -> tuple[str, str]:
    """Encode an HTML email payload into polymorphic MIME Content-Transfer-Encoding formats
    (quoted-printable, base64, 8bit) to disrupt static mail filter signatures.
    """
    import base64
    import quopri

    if encoding == "auto":
        encoding = random.choice(["quoted-printable", "8bit", "base64"])

    enc_lower = encoding.lower()
    raw_bytes = html_content.encode("utf-8")

    if enc_lower == "quoted-printable" or enc_lower == "qp":
        encoded = quopri.encodestring(raw_bytes).decode("ascii")
        return encoded, "quoted-printable"
    elif enc_lower == "base64" or enc_lower == "b64":
        b64_str = base64.b64encode(raw_bytes).decode("ascii")
        # Split into standard 76-character MIME chunks
        chunked = "\n".join(b64_str[i : i + 76] for i in range(0, len(b64_str), 76))
        return chunked, "base64"
    else:  # 8bit / standard
        return html_content, "8bit"


def generate_enterprise_message_id(domain: str, client_type: str = "auto") -> str:
    """Generate RFC 5322-compliant, entropy-salted Message-ID headers mimicking
    enterprise providers (Google Workspace, M365, Amazon SES) to satisfy SpamAssassin rules.
    """
    import email.utils

    d = domain.strip().lower()
    if "@" in d:
        d = d.split("@", 1)[1]
    if not d:
        d = "mailblinker.com"

    if client_type == "auto":
        client_type = random.choice(["google", "outlook", "ses"])

    if client_type == "google":
        rand_str = uuid.uuid4().hex[:16]
        return f"<CA{rand_str.upper()}@{d}>"
    elif client_type == "outlook":
        hex_id = uuid.uuid4().hex[:20].upper()
        return f"<{hex_id}DB7PR04MB4567@{d}>"
    else:  # ses / default
        msg_id = email.utils.make_msgid(domain=d)
        return msg_id


def generate_rfc2822_date() -> str:
    """Generate a standard RFC 2822 compliant Date header."""
    import email.utils

    return email.utils.formatdate(localtime=True)


def generate_feedback_id_headers(
    campaign_id: str = "general",
    user_id: str = "u1",
    sender_id: str = "mailblinker",
    provider_id: str = "mb",
) -> dict[str, str]:
    """Generate RFC 6578 / Google Postmaster compliant Feedback-ID and Abuse headers."""
    fbl_token = f"{campaign_id}:{user_id}:{sender_id}:{provider_id}"
    abuse_domain = sender_id if "." in sender_id else "mailblinker.com"
    return {
        "Feedback-ID": fbl_token,
        "X-Feedback-ID": fbl_token,
        "X-Complaints-To": f"abuse@{abuse_domain}",
    }


def encode_rfc2047_header(text: str, encoding: str = "B") -> str:
    """Encode a header string into RFC 2047 compliant format (=?utf-8?B?...?= or =?utf-8?Q?...?=)
    to protect non-ASCII subjects and display names from MTA corruption.
    """
    import base64
    import quopri

    if not any(ord(c) > 127 for c in text) and "\n" not in text and "\r" not in text:
        return text

    enc = encoding.upper()
    if enc == "B":
        b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return f"=?utf-8?B?{b64}?="
    else:  # "Q" (Quoted-Printable)
        qp = quopri.encodestring(text.encode("utf-8")).decode("ascii").strip()
        qp = qp.replace(" ", "_")
        return f"=?utf-8?Q?{qp}?="


def generate_autocrypt_headers(
    addr: str,
    keydata: str = "",
    prefer_encrypt: str = "mutual",
) -> dict[str, str]:
    """Generate RFC/Autocrypt Level 1 compliant End-to-End Encryption Discovery headers."""
    import base64

    clean_addr = addr.strip("<>").strip()
    if not keydata:
        synthetic_key = f"autocrypt-key-{clean_addr}".encode("utf-8")
        key_b64 = base64.b64encode(synthetic_key).decode("ascii")
    else:
        key_b64 = keydata.replace("\n", "").replace(" ", "").strip()

    autocrypt_value = f"addr={clean_addr}; prefer-encrypt={prefer_encrypt}; keydata={key_b64}"
    return {
        "Autocrypt": autocrypt_value,
    }


def generate_reply_thread_headers(
    parent_message_id: str,
    references: Optional[list[str]] = None,
) -> dict[str, str]:
    """Generate RFC 5322 In-Reply-To and References conversation thread headers
    to preserve grouping in Gmail/Outlook and earn SpamAssassin THREAD_MEMBER score.
    """
    clean_parent = parent_message_id.strip("<>").strip()
    ref_list: list[str] = []
    if references:
        for r in references:
            clean_r = r.strip("<>").strip()
            if clean_r:
                ref_list.append(f"<{clean_r}>")

    if f"<{clean_parent}>" not in ref_list:
        ref_list.append(f"<{clean_parent}>")

    return {
        "In-Reply-To": f"<{clean_parent}>",
        "References": " ".join(ref_list),
    }


def generate_internationalized_headers(
    lang_code: str = "en",
    script_direction: str = "ltr",
) -> dict[str, str]:
    """Generate RFC 6532 SMTPUTF8 internationalization and language localization headers
    to establish natural linguistic deliverability signals across multilingual mail exchangers.
    """
    clean_lang = lang_code.strip().lower() or "en"
    clean_dir = script_direction.strip().lower() or "ltr"
    return {
        "Content-Language": clean_lang,
        "Accept-Language": f"{clean_lang}, *;q=0.5",
        "X-Mailer-Script-Direction": clean_dir,
    }


def generate_arf_feedback_report(
    feedback_type: str = "abuse",
    user_agent: str = "MailBlinker-FBL/1.0",
    original_mail: str = "",
) -> dict[str, str]:
    """Generate RFC 5965 Abuse Reporting Format (ARF) message/feedback-report payload
    to simulate and test ISP Feedback Loop (FBL) complaint ingestion pipelines.
    """
    ts = int(time.time())
    body = (
        f"Feedback-Type: {feedback_type}\n"
        f"User-Agent: {user_agent}\n"
        f"Version: 1.0\n"
        f"Arrival-Date: {ts}\n"
    )
    if original_mail:
        body += f"\n--- Original Message Preview ---\n{original_mail[:200]}"

    return {
        "Content-Type": 'message/feedback-report; report-type="feedback-report"',
        "Feedback-Report": body,
    }


def encode_verp_address(return_path: str, recipient: str) -> str:
    """Encode an RFC 5321 Variable Envelope Return Path (VERP) bounce address
    (e.g., bounces+user=example.com@domain.com) for automated bounce attribution.
    """
    clean_rp = return_path.strip("<>").strip()
    clean_rcpt = recipient.strip("<>").strip()
    if "@" not in clean_rp or "@" not in clean_rcpt:
        return clean_rp

    rp_user, rp_domain = clean_rp.split("@", 1)
    verp_encoded_rcpt = clean_rcpt.replace("@", "=")
    return f"{rp_user}+{verp_encoded_rcpt}@{rp_domain}"


def decode_verp_address(verp_address: str) -> tuple[str, str]:
    """Decode an RFC 5321 VERP address back to (original_return_path, recipient_email)."""
    clean_addr = verp_address.strip("<>").strip()
    if "@" not in clean_addr or "+" not in clean_addr:
        return (clean_addr, "")

    local_part, domain = clean_addr.split("@", 1)
    if "+" not in local_part:
        return (clean_addr, "")

    base_user, verp_part = local_part.split("+", 1)
    if "=" in verp_part:
        rcpt_email = verp_part.replace("=", "@", 1)
        original_rp = f"{base_user}@{domain}"
        return (original_rp, rcpt_email)

    return (f"{base_user}@{domain}", "")
