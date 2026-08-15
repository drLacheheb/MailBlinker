from fastapi import APIRouter, Response

router = APIRouter()

FAVICON_ICO_BYTES = (
    b"\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x20\x00\x68\x04\x00\x00\x16\x00\x00\x00"
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa"
    b"\x00\x00\x00\x0bIDATx\x9cc`\x00\x02\x00\x00\x05\x00\x01z^\xab?\x00\x00\x00\x00IEND\xaeB`\x82"
)

ROBOTS_TXT_CONTENT = """User-agent: *
Disallow: /api/
Disallow: /assets/private/
Allow: /assets/
Allow: /cdn/
Allow: /static/
"""

SECURITY_TXT_CONTENT = """Contact: mailto:security@mailblinker.com
Expires: 2027-12-31T23:59:59.000Z
Preferred-Languages: en
Canonical: https://mailblinker.com/.well-known/security.txt
Policy: https://mailblinker.com/security
"""

SITEMAP_XML_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://mailblinker.com/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""


CDN_PORTAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CloudEdge • Global Content Delivery Network</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #090d16;
      color: #f1f5f9;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      padding: 24px;
      box-sizing: border-box;
    }
    .card {
      background: #111827;
      border: 1px solid #1f2937;
      border-radius: 16px;
      max-width: 520px;
      width: 100%;
      padding: 36px;
      box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
    }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      font-weight: 600;
      color: #10b981;
      background: rgba(16,185,129,0.1);
      padding: 4px 12px;
      border-radius: 9999px;
      margin-bottom: 20px;
    }
    .dot {
      width: 8px;
      height: 8px;
      background: #10b981;
      border-radius: 50%;
    }
    h1 {
      font-size: 22px;
      font-weight: 700;
      margin: 0 0 12px;
    }
    p {
      font-size: 14px;
      color: #94a3b8;
      line-height: 1.6;
      margin: 0 0 24px;
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      background: #0f172a;
      padding: 16px;
      border-radius: 10px;
    }
    .grid-item {
      font-size: 12px;
      color: #64748b;
    }
    .grid-val {
      font-size: 13px;
      font-weight: 600;
      color: #e2e8f0;
      margin-top: 2px;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="status"><span class="dot"></span> All Edge POPs Operational</div>
    <h1>CloudEdge Asset Gateway</h1>
    <p>High-performance globally distributed edge storage and static caching node.</p>
    <div class="grid">
      <div class="grid-item">Edge Region<div class="grid-val">FRA1 (Frankfurt)</div></div>
      <div class="grid-item">HTTP Protocol<div class="grid-val">HTTP/2 • TLS 1.3</div></div>
      <div class="grid-item">Edge Cache<div class="grid-val">Dynamic Sharding</div></div>
      <div class="grid-item">Propagation Latency<div class="grid-val">&lt; 15ms Avg</div></div>
    </div>
  </div>
</body>
</html>"""


@router.get("/", include_in_schema=False)
async def get_cdn_portal() -> Response:
    return Response(
        content=CDN_PORTAL_HTML,
        media_type="text/html; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Server": "cloudflare",
            "CF-Cache-Status": "HIT",
        },
    )


@router.get("/robots.txt", include_in_schema=False)
async def get_robots_txt() -> Response:
    return Response(
        content=ROBOTS_TXT_CONTENT,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "public, max-age=86400", "Server": "cloudflare"},
    )


@router.get("/favicon.ico", include_in_schema=False)
async def get_favicon() -> Response:
    return Response(
        content=FAVICON_ICO_BYTES,
        media_type="image/x-icon",
        headers={"Cache-Control": "public, max-age=86400", "Server": "cloudflare"},
    )


@router.get("/.well-known/security.txt", include_in_schema=False)
async def get_security_txt() -> Response:
    return Response(
        content=SECURITY_TXT_CONTENT,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "public, max-age=86400", "Server": "cloudflare"},
    )


@router.get("/sitemap.xml", include_in_schema=False)
async def get_sitemap_xml() -> Response:
    return Response(
        content=SITEMAP_XML_CONTENT,
        media_type="application/xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=86400", "Server": "cloudflare"},
    )
