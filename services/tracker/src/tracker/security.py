import time
from collections import defaultdict
from typing import Dict, List, Optional

from core import settings
from fastapi import Header, HTTPException, Request, Security, status
from fastapi.security.api_key import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware

api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header_scheme),
    header_key: Optional[str] = Header(None, alias="x-api-key"),
):
    if not settings.API_KEY:
        return True

    provided_key = api_key or header_key
    if provided_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key (X-API-Key header required)",
        )
    return True


class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int = 120):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60.0
        self._history: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        if not settings.RATE_LIMIT_ENABLED:
            return True

        now = time.time()
        cutoff = now - self.window_seconds
        client_history = [t for t in self._history[client_ip] if t > cutoff]
        self._history[client_ip] = client_history

        if len(client_history) >= self.requests_per_minute:
            return False

        client_history.append(now)
        return True


rate_limiter = InMemoryRateLimiter(requests_per_minute=120)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        if not rate_limiter.is_allowed(client_ip):
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        return response
