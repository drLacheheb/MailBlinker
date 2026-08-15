import pytest
from core import init_db, settings
from httpx import ASGITransport, AsyncClient
from tracker.main import app
from tracker.security import InMemoryRateLimiter


@pytest.mark.asyncio
async def test_security_headers_present():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        assert res.headers["x-content-type-options"] == "nosniff"
        assert res.headers["x-frame-options"] == "DENY"
        assert res.headers["x-xss-protection"] == "1; mode=block"
        assert "strict-origin" in res.headers["referrer-policy"]
        assert "max-age=31536000" in res.headers["strict-transport-security"]


@pytest.mark.asyncio
async def test_invalid_token_regex_sanitization():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/track/../../etc/passwd.gif")
        assert res.status_code in (400, 404, 422)

        res_xss = await ac.get("/track/<script>alert(1)</script>.gif")
        assert res_xss.status_code in (400, 404, 422)


@pytest.mark.asyncio
async def test_rate_limiter_logic():
    limiter = InMemoryRateLimiter(requests_per_minute=3)
    ip = "192.0.2.42"

    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is False


@pytest.mark.asyncio
async def test_api_key_protection_enforcement():
    await init_db()
    original_key = settings.API_KEY
    try:
        settings.API_KEY = "super-secret-key-12345"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_unauth = await ac.get("/api/emails")
            assert res_unauth.status_code == 401

            res_wrong = await ac.get(
                "/api/emails",
                headers={"X-API-Key": "wrong-key"},
            )
            assert res_wrong.status_code == 401

            res_valid = await ac.get(
                "/api/emails",
                headers={"X-API-Key": "super-secret-key-12345"},
            )
            assert res_valid.status_code == 200
    finally:
        settings.API_KEY = original_key
