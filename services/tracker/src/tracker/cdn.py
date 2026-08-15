import hashlib
from typing import Dict


def get_cdn_headers_for_token(token: str) -> Dict[str, str]:
    """Deterministically select a realistic CDN response header profile based on token hash."""
    seed = sum(ord(c) for c in token)
    cdn_choice = seed % 3
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    base_headers = {
        "Cache-Control": (
            "no-cache, no-store, must-revalidate, max-age=0, private, proxy-revalidate"
        ),
        "Pragma": "no-cache",
        "Expires": "0",
        "ETag": f'"{token}"',
        "Vary": "Accept-Encoding, Accept",
    }

    if cdn_choice == 0:
        # Cloudflare Edge Profile
        return {
            **base_headers,
            "Server": "cloudflare",
            "CF-Cache-Status": "DYNAMIC",
            "CF-Ray": f"{token_hash[:16]}-FRA",
            "CF-Edge-Cache": "HIT",
            "Server-Timing": f"cfRequestDuration;dur={14 + (seed % 12)}.{(seed % 9)}",
            "Accept-Ranges": "bytes",
        }
    elif cdn_choice == 1:
        # AWS CloudFront Edge Profile
        return {
            **base_headers,
            "Server": "CloudFront",
            "X-Cache": "Miss from cloudfront",
            "X-Amz-Cf-Pop": "FRA50-P1",
            "X-Amz-Cf-Id": f"{token_hash[:24]}==",
            "Server-Timing": f"cdn-cache;desc=MISS, edge;dur={10 + (seed % 10)}.{(seed % 7)}",
            "Accept-Ranges": "bytes",
        }
    else:
        # Fastly / Varnish Edge Profile
        return {
            **base_headers,
            "Server": "varnish",
            "X-Served-By": f"cache-fra-eddf{token_hash[:8]}-FRA",
            "X-Cache": "MISS",
            "Via": "1.1 varnish",
            "Server-Timing": f"fastly;dur={8 + (seed % 8)}.{(seed % 6)}",
            "Accept-Ranges": "bytes",
        }
