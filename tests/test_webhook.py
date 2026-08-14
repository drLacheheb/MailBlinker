import pytest
from core import init_db, settings
from httpx import ASGITransport, AsyncClient
from tracker.main import app


@pytest.mark.asyncio
async def test_webhook_endpoint():
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test health endpoints
        for path in ["/", "/health", "/healthz"]:
            res = await ac.get(path)
            assert res.status_code == 200
            assert res.json()["status"] == "healthy"

        # Test valid webhook update ping
        update_payload = {
            "update_id": 10001,
            "message": {
                "message_id": 1,
                "date": 1441645532,
                "chat": {
                    "id": 111111,
                    "type": "private",
                    "first_name": "TestUser",
                },
                "text": "/start",
            },
        }

        webhook_res = await ac.post("/api/webhook/telegram", json=update_payload)
        assert webhook_res.status_code == 200

        # Test secret token verification
        settings.TELEGRAM_WEBHOOK_SECRET = "super-secret-token"
        try:
            # Unauthorized request without secret
            unauth_res = await ac.post("/api/webhook/telegram", json=update_payload)
            assert unauth_res.status_code == 403

            # Authorized request with secret
            auth_res = await ac.post(
                "/api/webhook/telegram",
                json=update_payload,
                headers={"X-Telegram-Bot-Api-Secret-Token": "super-secret-token"},
            )
            assert auth_res.status_code == 200
        finally:
            settings.TELEGRAM_WEBHOOK_SECRET = None
