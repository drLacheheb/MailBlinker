import hashlib

import pytest
from core import init_db
from httpx import ASGITransport, AsyncClient
from tracker.constants import build_dynamic_png
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
        assert stealth_res.content.startswith(b"\x89PNG")
        assert len(stealth_res.content) > 50
        assert stealth_res.headers["server"].lower() in ("cloudflare", "cloudfront", "varnish")
        assert stealth_res.headers["accept-ranges"] == "bytes"
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

        # 4. Test HTTP 304 Not Modified with If-None-Match ETag re-validation
        etag = stealth_res.headers["etag"]
        reval_res = await ac.get(
            relative_pixel_path,
            headers={"User-Agent": "GoogleImageProxy", "If-None-Match": etag},
        )
        assert reval_res.status_code == 304
        assert len(reval_res.content) == 0

        # 5. Test Smart Accept Header Negotiation (WebP)
        webp_res = await ac.get(
            f"/assets/signature/{token}",
            headers={"User-Agent": "Mozilla/5.0", "Accept": "image/webp,image/*"},
        )
        assert webp_res.status_code == 200
        assert webp_res.headers["content-type"] == "image/webp"

        # 6. Test Dynamic PNG SHA-256 Checksum Uniqueness
        png1 = build_dynamic_png("token_alpha_111")
        png2 = build_dynamic_png("token_beta_222")
        assert png1.startswith(b"\x89PNG")
        assert png2.startswith(b"\x89PNG")
        assert hashlib.sha256(png1).hexdigest() != hashlib.sha256(png2).hexdigest()

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

        # 7. Test CDN Decoy Endpoints
        robots_res = await ac.get("/robots.txt")
        assert robots_res.status_code == 200
        assert "Disallow: /api/" in robots_res.text
        assert robots_res.headers["server"] == "cloudflare"

        favicon_res = await ac.get("/favicon.ico")
        assert favicon_res.status_code == 200
        assert favicon_res.headers["content-type"] == "image/x-icon"

        security_res = await ac.get("/.well-known/security.txt")
        assert security_res.status_code == 200
        assert "Contact:" in security_res.text

        sitemap_res = await ac.get("/sitemap.xml")
        assert sitemap_res.status_code == 200
        assert "<urlset" in sitemap_res.text

        # 8. Test Honeypot Canary Trap
        canary_res = await ac.get(f"/cdn/verify/chk_{token}.png")
        assert canary_res.status_code == 204
        assert canary_res.headers["server"].lower() in ("cloudflare", "cloudfront", "varnish")

        # 9. Test Semantic Link Click Tracking & Safe Redirection
        link_res = await ac.get(
            f"/l/{token}?dest=https%3A%2F%2Fexample.com%2Fproposal.pdf",
            follow_redirects=False,
        )
        assert link_res.status_code == 302
        assert link_res.headers["location"] == "https://example.com/proposal.pdf"
        assert link_res.headers["server"].lower() in ("cloudflare", "cloudfront", "varnish")

        # 10. Test Open Redirect Protection on Invalid Scheme
        bad_link_res = await ac.get(
            f"/l/{token}?dest=javascript:alert(1)",
            follow_redirects=False,
        )
        assert bad_link_res.status_code == 400

        # 11. Test DNS Deliverability API Tool Endpoint
        dns_res = await ac.get("/api/tools/dns-check?domain=gmail.com")
        assert dns_res.status_code == 200
        dns_data = dns_res.json()
        assert dns_data["domain"] == "gmail.com"
        assert dns_data["score"] >= 50
        assert dns_data["mx_valid"] is True

        # 12. Test Token Burst Throttle & Anti-Replay Shield
        from tracker.throttle import TokenBurstShield

        shield = TokenBurstShield(max_requests=3, window_seconds=5.0)
        test_tok = "burst_token_xyz"
        assert shield.is_bursting(test_tok) is False
        assert shield.is_bursting(test_tok) is False
        assert shield.is_bursting(test_tok) is False
        assert shield.is_bursting(test_tok) is True
