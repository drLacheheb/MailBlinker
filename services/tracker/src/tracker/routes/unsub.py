from core import AsyncSessionLocal, SqlAlchemyEmailRepository
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/unsub", tags=["Unsubscribe"])


@router.post("/{token}", include_in_schema=False)
async def rfc8058_one_click_unsubscribe(token: str) -> Response:
    """RFC 8058 One-Click List-Unsubscribe handler for automated mail clients."""
    clean_token = token.split("_", 1)[1] if "_" in token else token
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        email = await repo.get_by_token(clean_token)
        if not email or email.id is None:
            raise HTTPException(status_code=404, detail="Email tracker not found")

        await repo.update_notify_settings(
            email_id=email.id, limit=0, update_limit=True, notify_forwarding=False
        )

    return Response(
        content='{"status":"unsubscribed","mode":"rfc8058_one_click"}',
        media_type="application/json",
        status_code=200,
    )


@router.get("/{token}", response_class=HTMLResponse, include_in_schema=False)
async def web_unsubscribe_page(token: str) -> HTMLResponse:
    """Web-based unsubscribe confirmation page for human recipients."""
    clean_token = token.split("_", 1)[1] if "_" in token else token
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)
        email = await repo.get_by_token(clean_token)
        if email and email.id is not None:
            await repo.update_notify_settings(
                email_id=email.id, limit=0, update_limit=True, notify_forwarding=False
            )

    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Unsubscribed Successfully</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
           background: #f8fafc; color: #1e293b; display: flex; align-items: center;
           justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }
    .card { background: #fff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            max-width: 440px; width: 100%; padding: 32px; text-align: center; }
    .icon { font-size: 48px; margin-bottom: 16px; }
    h1 { font-size: 20px; font-weight: 700; margin: 0 0 8px; color: #0f172a; }
    p { font-size: 14px; color: #64748b; margin: 0; line-height: 1.5; }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✅</div>
    <h1>Unsubscribed Successfully</h1>
    <p>You will no longer receive notifications or tracking events for this email thread.</p>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=200)
