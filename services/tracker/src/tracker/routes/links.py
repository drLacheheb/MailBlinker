import base64
import json
import re
import urllib.parse
from datetime import datetime, timezone

from core import RecordOpenDTO, RecordOpenUseCase
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from ..cdn import get_cdn_headers_for_token
from ..dependencies import get_record_open_use_case
from ..security import get_client_ip

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
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "Unknown") if request else "Unknown"
    accept_language = request.headers.get("accept-language") if request else None

    # Headless Browser Sandbox Trap (detects automated sandbox runners before 302 redirect)
    ua_lower = user_agent.lower()
    is_headless_sandbox = (
        "headless" in ua_lower
        or "phantomjs" in ua_lower
        or "puppeteer" in ua_lower
        or "playwright" in ua_lower
        or (not accept_language and "linux" in ua_lower and "chrome" in ua_lower)
    )
    if is_headless_sandbox:
        user_agent = f"{user_agent} [Headless Sandbox Probe]"

    dto = RecordOpenDTO(
        token=clean_token,
        open_time=open_time,
        client_ip=client_ip,
        user_agent=user_agent,
        accept_language=accept_language,
    )
    await use_case.execute(dto)

    headers = get_cdn_headers_for_token(clean_token)
    return RedirectResponse(url=dest, status_code=302, headers=headers)


@router.get("/cdn/go/{payload}", include_in_schema=False)
async def track_and_redirect_cloaked(
    payload: str,
    request: Request = None,  # type: ignore
    use_case: RecordOpenUseCase = Depends(get_record_open_use_case),
) -> RedirectResponse:
    try:
        padded = payload + "=" * (-len(payload) % 4)
        raw_bytes = base64.urlsafe_b64decode(padded.encode("ascii"))
        data = json.loads(raw_bytes.decode("utf-8"))
        token = data.get("t", "")
        dest = data.get("u", "")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload encoding")

    return await track_and_redirect_link(token=token, dest=dest, request=request, use_case=use_case)
