import asyncio
import random
import re
from datetime import datetime, timezone

from core import RecordOpenDTO, RecordOpenUseCase
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ..cdn import get_cdn_headers_for_token
from ..constants import (
    build_dynamic_apng,
    build_dynamic_avif,
    build_dynamic_gif,
    build_dynamic_png,
    build_dynamic_svg,
    build_dynamic_webp,
)
from ..dependencies import get_record_open_use_case
from ..throttle import token_burst_shield

router = APIRouter()
SAFE_TOKEN_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")


def _extract_token_and_format(
    filename: str, request_path: str = "", accept_header: str = ""
) -> tuple[str, str, bytes]:
    """Extract clean token, media_type, and image bytes with dynamic hashing
    and format negotiation.
    """
    path_lower = request_path.lower()
    if filename.endswith(".gif") or path_lower.endswith(".gif"):
        ext = "gif"
        raw = filename[:-4] if filename.endswith(".gif") else filename
    elif filename.endswith(".svg") or path_lower.endswith(".svg"):
        ext = "svg"
        raw = filename[:-4] if filename.endswith(".svg") else filename
    elif filename.endswith(".webp") or path_lower.endswith(".webp"):
        ext = "webp"
        raw = filename[:-5] if filename.endswith(".webp") else filename
    elif filename.endswith(".avif") or path_lower.endswith(".avif"):
        ext = "avif"
        raw = filename[:-5] if filename.endswith(".avif") else filename
    elif filename.endswith(".apng") or path_lower.endswith(".apng"):
        ext = "apng"
        raw = filename[:-5] if filename.endswith(".apng") else filename
    elif filename.endswith(".png") or path_lower.endswith(".png"):
        ext = "png"
        raw = filename[:-4] if filename.endswith(".png") else filename
    elif "image/avif" in accept_header.lower():
        ext = "avif"
        raw = filename
    elif "image/webp" in accept_header.lower():
        ext = "webp"
        raw = filename
    elif "image/svg+xml" in accept_header.lower():
        ext = "svg"
        raw = filename
    else:
        ext = "png"
        raw = filename

    # Strip semantic prefixes (e.g., sig_token123 -> token123)
    if "_" in raw:
        clean_token = raw.split("_", 1)[1]
    else:
        clean_token = raw

    if ext == "gif":
        media_type = "image/gif"
        content = build_dynamic_gif(clean_token)
    elif ext == "svg":
        media_type = "image/svg+xml"
        content = build_dynamic_svg(clean_token)
    elif ext == "webp":
        media_type = "image/webp"
        content = build_dynamic_webp(clean_token)
    elif ext == "avif":
        media_type = "image/avif"
        content = build_dynamic_avif(clean_token)
    elif ext == "apng":
        media_type = "image/png"
        content = build_dynamic_apng(clean_token)
    else:
        media_type = "image/png"
        content = build_dynamic_png(clean_token)

    return clean_token, media_type, content


async def _handle_pixel_tracking(
    filename: str,
    request: Request,
    use_case: RecordOpenUseCase,
) -> Response:
    accept_hdr = request.headers.get("accept", "")
    clean_token, media_type, content = _extract_token_and_format(
        filename, request.url.path, accept_hdr
    )

    if not SAFE_TOKEN_PATTERN.match(clean_token):
        raise HTTPException(status_code=400, detail="Invalid token format")

    open_time = datetime.now(timezone.utc)
    client_ip = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("user-agent", "Unknown")
    accept_language = request.headers.get("accept-language")
    purpose = (
        request.headers.get("sec-purpose")
        or request.headers.get("purpose")
        or request.headers.get("x-purpose")
    )
    client_hints = {
        k.lower(): v for k, v in request.headers.items() if k.lower().startswith("sec-ch-ua")
    }
    tls_version = (
        request.headers.get("x-tls-version")
        or request.headers.get("ssl-protocol")
        or str(request.scope.get("tls_version") or "")
        or None
    )

    # Anti-replay token burst rate limiting
    if not token_burst_shield.is_bursting(clean_token):
        dto = RecordOpenDTO(
            token=clean_token,
            open_time=open_time,
            client_ip=client_ip,
            user_agent=user_agent,
            accept_language=accept_language,
            purpose=purpose,
            client_hints=client_hints,
            tls_version=tls_version,
        )
        await use_case.execute(dto)

    headers = get_cdn_headers_for_token(clean_token)
    etag_val = headers.get("ETag", f'"{clean_token}"')

    # Humanized CDN edge propagation micro-jitter (10-25ms)
    await asyncio.sleep(random.uniform(0.010, 0.025))

    # HTTP 304 Not Modified support for ETag re-validation
    if_none_match = request.headers.get("if-none-match")
    if if_none_match and (
        if_none_match.strip() == etag_val
        or if_none_match.strip() == "*"
        or if_none_match.strip('"') == clean_token
    ):
        return Response(status_code=304, headers=headers)

    # HEAD request support
    if request.method == "HEAD":
        return Response(status_code=200, headers=headers, media_type=media_type)

    # HTTP 206 Partial Content (Range request support for CDN byte-serving emulation)
    range_header = request.headers.get("range")
    if range_header and range_header.startswith("bytes="):
        try:
            range_spec = range_header[6:].split("-")[0]
            start = int(range_spec) if range_spec else 0
            sliced = content[start:]
            headers["Content-Range"] = f"bytes {start}-{len(content) - 1}/{len(content)}"
            return Response(
                content=sliced,
                status_code=206,
                media_type=media_type,
                headers=headers,
            )
        except Exception:
            pass

    return Response(
        content=content,
        media_type=media_type,
        headers=headers,
    )


@router.api_route("/assets/{category}/{filename}", methods=["GET", "HEAD"])
@router.api_route("/cdn/{category}/{filename}", methods=["GET", "HEAD"])
@router.api_route("/static/{category}/{filename}", methods=["GET", "HEAD"])
async def track_stealth_pixel(
    category: str,
    filename: str,
    request: Request,
    use_case: RecordOpenUseCase = Depends(get_record_open_use_case),
):
    del category  # Unused path parameter placeholder
    return await _handle_pixel_tracking(filename, request, use_case)


@router.api_route("/track/{token}", methods=["GET", "HEAD"])
@router.api_route("/track/{token}.gif", methods=["GET", "HEAD"])
async def track_pixel_legacy(
    token: str,
    request: Request,
    use_case: RecordOpenUseCase = Depends(get_record_open_use_case),
):
    return await _handle_pixel_tracking(token, request, use_case)
