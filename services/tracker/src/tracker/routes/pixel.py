import re
from datetime import datetime, timezone

from core import RecordOpenDTO, RecordOpenUseCase
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ..constants import TRANSPARENT_1X1_GIF, TRANSPARENT_1X1_PNG
from ..dependencies import get_record_open_use_case

router = APIRouter()
SAFE_TOKEN_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")


def _extract_token_and_format(filename: str, request_path: str = "") -> tuple[str, str, bytes]:
    """Extract clean token, media_type, and image bytes from semantic camouflage filenames."""
    path_lower = request_path.lower()
    if filename.endswith(".gif") or path_lower.endswith(".gif"):
        ext = "gif"
        raw = filename[:-4] if filename.endswith(".gif") else filename
    elif filename.endswith(".png") or path_lower.endswith(".png"):
        ext = "png"
        raw = filename[:-4] if filename.endswith(".png") else filename
    else:
        ext = "png"
        raw = filename

    # Strip semantic prefixes like sig_, logo_, badge_, spacer_, brand_, icon_, photo_, glyph_
    if "_" in raw:
        clean_token = raw.split("_", 1)[1]
    else:
        clean_token = raw

    media_type = "image/png" if ext == "png" else "image/gif"
    content = TRANSPARENT_1X1_PNG if ext == "png" else TRANSPARENT_1X1_GIF
    return clean_token, media_type, content


async def _handle_pixel_tracking(
    filename: str,
    request: Request,
    use_case: RecordOpenUseCase,
) -> Response:
    clean_token, media_type, content = _extract_token_and_format(filename, request.url.path)

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
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Cache-Control": cache_header,
            "Pragma": "no-cache",
            "Expires": "0",
            "ETag": f'"{clean_token}-{int(open_time.timestamp())}"',
        },
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
