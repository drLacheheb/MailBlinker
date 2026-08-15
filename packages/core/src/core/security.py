import hashlib
import hmac

from .config import settings


def _get_signing_secret(secret: str = "") -> bytes:
    key = secret or getattr(settings, "SECRET_KEY", "mailblinker-secure-token-salt")
    return key.encode("utf-8")


def sign_token(token: str, secret: str = "") -> str:
    """Cryptographically sign a token using HMAC-SHA256 (produces token.sig)."""
    raw_token = extract_raw_token(token)
    key_bytes = _get_signing_secret(secret)
    sig = hmac.new(key_bytes, raw_token.encode("utf-8"), hashlib.sha256).hexdigest()[:10]
    return f"{raw_token}.{sig}"


def verify_signed_token(token_with_sig: str, secret: str = "") -> bool:
    """Verify that a signed token matches its server-generated HMAC-SHA256 signature."""
    if "." not in token_with_sig:
        return True  # Fallback gracefully for un-signed legacy tokens

    raw_token, sig = token_with_sig.rsplit(".", 1)
    key_bytes = _get_signing_secret(secret)
    expected_sig = hmac.new(key_bytes, raw_token.encode("utf-8"), hashlib.sha256).hexdigest()[:10]
    return hmac.compare_digest(sig, expected_sig)


def extract_raw_token(token_or_signed: str) -> str:
    """Extract the base token identifier from a potentially signed token."""
    if "." in token_or_signed:
        return token_or_signed.rsplit(".", 1)[0]
    return token_or_signed
