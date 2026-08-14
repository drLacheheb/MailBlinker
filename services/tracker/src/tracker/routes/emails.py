from core import (
    CreateEmailDTO,
    CreateEmailUseCase,
    DeleteEmailUseCase,
    ListEmailsUseCase,
)
from fastapi import APIRouter, Depends, HTTPException
from formatter import EmailLink

from ..dependencies import (
    get_create_email_use_case,
    get_delete_email_use_case,
    get_list_emails_use_case,
)
from ..schemas import CreateEmailRequest
from ..security import verify_api_key

router = APIRouter(
    prefix="/api/emails",
    tags=["emails"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("")
async def create_tracked_email(
    payload: CreateEmailRequest,
    use_case: CreateEmailUseCase = Depends(get_create_email_use_case),
):
    links_list = (
        [EmailLink(text=lnk.text, url=lnk.url) for lnk in payload.links] if payload.links else []
    )
    dto = CreateEmailDTO(
        title=payload.title,
        recipient_email=payload.recipient_email,
        recipient_name=payload.recipient_name,
        sender_name=payload.sender_name,
        subject=payload.subject,
        body_text=payload.body_text,
        custom_html=payload.custom_html,
        links=links_list,
    )
    result = await use_case.execute(dto)

    return {
        "id": result.email.id,
        "token": result.email.token,
        "pixel_url": result.pixel_url,
        "title": result.email.title,
        "subject": result.email.subject,
        "formatted_html": result.formatted_html,
    }


@router.get("")
async def list_tracked_emails(
    use_case: ListEmailsUseCase = Depends(get_list_emails_use_case),
):
    emails = await use_case.execute()

    return [
        {
            "id": e.id,
            "token": e.token,
            "title": e.title,
            "recipient_email": e.recipient_email,
            "recipient_name": e.recipient_name,
            "subject": e.subject,
            "created_at": e.created_at.isoformat(),
            "first_opened_at": e.first_opened_at.isoformat() if e.first_opened_at else None,
            "last_opened_at": e.last_opened_at.isoformat() if e.last_opened_at else None,
            "open_count": e.open_count,
            "events_count": len(e.events),
            "events": [
                {
                    "id": ev.id,
                    "timestamp": ev.timestamp.isoformat(),
                    "ip_address": ev.ip_address,
                    "country": ev.country,
                    "region": ev.region,
                    "city": ev.city,
                    "isp": ev.isp,
                    "device_model": ev.device_model,
                    "os_name": ev.os_name,
                    "browser_name": ev.browser_name,
                    "language": ev.language,
                    "user_agent": ev.user_agent,
                    "elapsed_seconds": ev.elapsed_seconds,
                }
                for ev in e.events
            ],
        }
        for e in emails
    ]


@router.delete("/{email_id}")
async def delete_tracked_email(
    email_id: int,
    use_case: DeleteEmailUseCase = Depends(get_delete_email_use_case),
):
    deleted = await use_case.execute(email_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tracked email not found")

    return {"status": "deleted", "id": email_id}
