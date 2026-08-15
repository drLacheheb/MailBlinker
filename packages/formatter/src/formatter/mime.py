import random
import time
import uuid


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
