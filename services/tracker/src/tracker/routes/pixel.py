import re
from datetime import datetime, timezone

from core import RecordOpenDTO, RecordOpenUseCase
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ..constants import TRANSPARENT_1X1_GIF
from ..dependencies import get_record_open_use_case

router = APIRouter()
SAFE_TOKEN_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")


@router.get("/track/{token}")
@router.get("/track/{token}.gif")
async def track_pixel(
    token: str,
    request: Request,
    use_case: RecordOpenUseCase = Depends(get_record_open_use_case),
):
    clean_token = token[:-4] if token.endswith(".gif") else token

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
        content=TRANSPARENT_1X1_GIF,
        media_type="image/gif",
        headers={
            "Cache-Control": cache_header,
            "Pragma": "no-cache",
            "Expires": "0",
            "ETag": f'"{clean_token}-{int(open_time.timestamp())}"',
        },
    )
