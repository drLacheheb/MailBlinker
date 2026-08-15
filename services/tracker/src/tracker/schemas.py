from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class EmailLinkSchema(BaseModel):
    text: str
    url: str


class CreateEmailRequest(BaseModel):
    title: str
    recipient_email: str
    recipient_name: Optional[str] = None
    sender_name: Optional[str] = None
    subject: Optional[str] = None
    body_text: Optional[str] = None
    custom_html: Optional[str] = None
    links: Optional[List[EmailLinkSchema]] = None
    telegram_chat_id: Optional[str] = None


class OpenEventSchema(BaseModel):
    id: Optional[int]
    timestamp: datetime
    ip_address: Optional[str]
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    device_model: Optional[str] = None
    os_name: Optional[str] = None
    browser_name: Optional[str] = None
    language: Optional[str] = None
    user_agent: Optional[str] = None
    elapsed_seconds: Optional[float] = None


class TrackedEmailSchema(BaseModel):
    id: Optional[int]
    token: str
    title: str
    recipient_email: str
    recipient_name: Optional[str]
    subject: Optional[str]
    telegram_chat_id: Optional[str] = None
    created_at: datetime
    first_opened_at: Optional[datetime]
    last_opened_at: Optional[datetime]
    open_count: int
    events: List[OpenEventSchema] = []
