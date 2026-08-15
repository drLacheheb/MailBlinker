import asyncio
import random
import re
from datetime import datetime, timezone

from core import RecordOpenDTO, RecordOpenUseCase
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ..constants import (
    TRANSPARENT_1X1_GIF,
    TRANSPARENT_1X1_WEBP,
    build_dynamic_png,
)
from ..dependencies import get_record_open_use_case

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
    elif filename.endswith(".png") or path_lower.endswith(".png"):
        ext = "png"
        raw = filename[:-4] if filename.endswith(".png") else filename
    elif "image/webp" in accept_header.lower():
        ext = "webp"
        raw = filename
    else:
        ext = "png"
        raw = filename

    # Strip semantic prefixes like sig_, logo_, badge_, spacer_, brand_, icon_, photo_, glyph_
    if "_" in raw:
        clean_token = raw.split("_", 1)[1]
    else:
        clean_token = raw

    if ext == "gif":
        media_type = "image/gif"
        content = TRANSPARENT_1X1_GIF
    elif ext == "webp":
        media_type = "image/webp"
        content = TRANSPARENT_1X1_WEBP
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

    dto = RecordOpenDTO(
        token=clean_token,
        open_time=open_time,
        client_ip=client_ip,
        user_agent=user_agent,
        accept_language=accept_language,
    )
    await use_case.execute(dto)

    cache_header = "no-cache, no-store, must-revalidate, max-age=0, private, proxy-revalidate"
    etag_val = f'"{clean_token}"'
    headers = {
        "Server": "cloudflare",
        "CF-Cache-Status": "DYNAMIC",
        "CF-Ray": f"{clean_token[:16]}-FRA",
        "Accept-Ranges": "bytes",
        "Vary": "Accept-Encoding, Accept",
        "Cache-Control": cache_header,
        "Pragma": "no-cache",
        "Expires": "0",
        "ETag": etag_val,
    }

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

    return Response(
        content=content,
        media_type=media_type,
        headers=headers,
    )


@router.get("/assets/{category}/{filename}")
@router.get("/cdn/{category}/{filename}")
@router.get("/static/{category}/{filename}")
async def track_stealth_pixel(
    category: str,
    filename: str,
    request: Request,
    use_case: RecordOpenUseCase = Depends(get_record_open_use_case),
):
    return await _handle_pixel_tracking(filename, request, use_case)


@router.get("/track/{token}")
@router.get("/track/{token}.gif")
async def track_pixel_legacy(
    token: str,
    request: Request,
    use_case: RecordOpenUseCase = Depends(get_record_open_use_case),
):
    return await _handle_pixel_tracking(token, request, use_case)
