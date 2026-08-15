import pytest
from core import init_db
from httpx import ASGITransport, AsyncClient
from tracker.main import app


@pytest.mark.asyncio
async def test_tracker_api_flow():
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_payload = {
            "title": "Client Proposal",
            "recipient_email": "client@example.com",
            "recipient_name": "Sarah",
            "sender_name": "Alex Dupont",
            "body_text": "Here is the proposal.",
        }
        res = await ac.post("/api/emails", json=create_payload)
        assert res.status_code == 200
        data = res.json()
        assert "token" in data
        assert "pixel_url" in data
        assert "formatted_html" in data
        token = data["token"]
        pixel_url = data["pixel_url"]

        # 1. Fetch generated stealth pixel URL (e.g. /assets/signature/sig_xxx.png)
        relative_pixel_path = "/" + pixel_url.split("/", 3)[-1]
        stealth_res = await ac.get(
            relative_pixel_path,
            headers={"User-Agent": "GoogleImageProxy"},
        )
        assert stealth_res.status_code == 200
        assert stealth_res.headers["content-type"] == "image/png"
        assert len(stealth_res.content) == 67
        assert "no-cache" in stealth_res.headers["cache-control"]
        assert "etag" in stealth_res.headers

        # 2. Test other semantic camouflage routes
        patterns_to_test = [
            f"/assets/signature/sig_{token}.png",
            f"/cdn/media/logo_{token}.png",
            f"/static/images/badge_{token}.png",
            f"/assets/img/spacer_{token}.png",
            f"/cdn/fonts/glyph_{token}.png",
        ]
        for path in patterns_to_test:
            resp = await ac.get(path, headers={"User-Agent": "GoogleImageProxy"})
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "image/png"

        # 3. Test legacy fallback /track/{token}.gif
        legacy_res = await ac.get(
            f"/track/{token}.gif",
            headers={"User-Agent": "GoogleImageProxy"},
        )
        assert legacy_res.status_code == 200
        assert legacy_res.headers["content-type"] == "image/gif"
        assert len(legacy_res.content) == 43

        list_res = await ac.get("/api/emails")
        assert list_res.status_code == 200
        emails = list_res.json()
        assert len(emails) >= 1

        target_email = next(e for e in emails if e["token"] == token)
        assert target_email["open_count"] >= 1
        assert len(target_email["events"]) >= 1

        health_res = await ac.get("/")
        assert health_res.status_code == 200
        assert health_res.json()["service"] == "MailBlinker API"
