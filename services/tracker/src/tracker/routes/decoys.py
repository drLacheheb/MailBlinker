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
