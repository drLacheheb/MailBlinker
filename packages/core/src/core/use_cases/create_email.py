import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from formatter import (
    EmailLink,
    EmailPayload,
    format_email,
    get_stealth_pixel_url,
    inject_tracking_tags,
)

from ..config import settings
from ..domain.entities import TrackedEmailEntity
from ..domain.interfaces import EmailRepositoryInterface


@dataclass
class CreateEmailDTO:
    title: str
    recipient_email: str
    recipient_name: Optional[str] = None
    sender_name: Optional[str] = None
    subject: Optional[str] = None
    body_text: Optional[str] = None
    custom_html: Optional[str] = None
    links: Optional[List[EmailLink]] = None
    telegram_chat_id: Optional[str] = None
    ttl_days: Optional[int] = None


@dataclass
class CreateEmailResult:
    email: TrackedEmailEntity
    pixel_url: str
    formatted_html: str


class CreateEmailUseCase:
    def __init__(self, repository: EmailRepositoryInterface, base_url: str = settings.BASE_URL):
        self._repository = repository
        self._base_url = base_url

    async def execute(self, dto: CreateEmailDTO) -> CreateEmailResult:
        token = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=dto.ttl_days) if dto.ttl_days else None

        email_entity = TrackedEmailEntity(
            id=None,
            token=token,
            title=dto.title,
            recipient_email=dto.recipient_email,
            recipient_name=dto.recipient_name,
            subject=dto.subject or dto.title,
            telegram_chat_id=dto.telegram_chat_id,
            created_at=now,
            expires_at=expires_at,
        )
        saved_email = await self._repository.create(email_entity)

        if dto.custom_html:
            formatted_html = inject_tracking_tags(dto.custom_html, token, self._base_url)
        else:
            payload = EmailPayload(
                title=dto.title,
                recipient_name=dto.recipient_name,
                sender_name=dto.sender_name,
                body_text=dto.body_text or f"Regarding: {dto.title}",
                links=dto.links or [],
            )
            formatted_html = format_email(payload, token, self._base_url)

        pixel_url = get_stealth_pixel_url(token, self._base_url)

        return CreateEmailResult(
            email=saved_email,
            pixel_url=pixel_url,
            formatted_html=formatted_html,
        )
