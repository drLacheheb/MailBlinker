import re
import urllib.parse
from datetime import datetime, timezone

from core import RecordOpenDTO, RecordOpenUseCase
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from ..dependencies import get_record_open_use_case

router = APIRouter()
SAFE_TOKEN_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")


def _is_safe_url(url: str) -> bool:
    """Ensure destination URL is an absolute http/https web link to prevent open redirects."""
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


@router.get("/l/{token}", include_in_schema=False)
@router.get("/cdn/link/{token}", include_in_schema=False)
async def track_and_redirect_link(
    token: str,
    dest: str = Query(..., description="Target destination URL"),
    request: Request = None,  # type: ignore
    use_case: RecordOpenUseCase = Depends(get_record_open_use_case),
) -> RedirectResponse:
    clean_token = token
    if "_" in token:
        clean_token = token.split("_", 1)[1]

    if not SAFE_TOKEN_PATTERN.match(clean_token):
        raise HTTPException(status_code=400, detail="Invalid token format")

    if not _is_safe_url(dest):
        raise HTTPException(status_code=400, detail="Invalid or unsafe destination URL")

    open_time = datetime.now(timezone.utc)
    client_ip = request.client.host if (request and request.client) else "Unknown"
    user_agent = request.headers.get("user-agent", "Unknown") if request else "Unknown"
    accept_language = request.headers.get("accept-language") if request else None

    dto = RecordOpenDTO(
        token=clean_token,
        open_time=open_time,
        client_ip=client_ip,
        user_agent=user_agent,
        accept_language=accept_language,
    )
    await use_case.execute(dto)

    headers = {
        "Server": "cloudflare",
        "CF-Ray": f"{clean_token[:16]}-FRA",
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0, private",
    }
    return RedirectResponse(url=dest, status_code=302, headers=headers)
