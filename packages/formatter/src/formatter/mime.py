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
