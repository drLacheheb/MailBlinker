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

        pixel_res = await ac.get(
            f"/track/{token}.gif",
            headers={"User-Agent": "GoogleImageProxy"},
        )
        assert pixel_res.status_code == 200
        assert pixel_res.headers["content-type"] == "image/gif"
        assert len(pixel_res.content) == 43

        assert "no-cache" in pixel_res.headers["cache-control"]
        assert "no-store" in pixel_res.headers["cache-control"]
        assert pixel_res.headers["pragma"] == "no-cache"
        assert "etag" in pixel_res.headers

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
