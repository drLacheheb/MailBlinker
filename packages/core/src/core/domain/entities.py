from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class OpenEventEntity:
    id: Optional[int]
    email_id: int
    timestamp: datetime
    ip_address: Optional[str] = None
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


@dataclass
class UserEntity:
    id: Optional[int]
    telegram_chat_id: str
    telegram_username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    default_notify_limit: Optional[int] = None
    default_notify_forwarding: bool = True
    timezone: str = "UTC"
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TrackedEmailEntity:
    id: Optional[int]
    token: str
    title: str
    recipient_email: str
    recipient_name: Optional[str] = None
    subject: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    first_opened_at: Optional[datetime] = None
    last_opened_at: Optional[datetime] = None
    open_count: int = 0
    notify_limit: Optional[int] = None
    notify_forwarding: bool = True
    events: List[OpenEventEntity] = field(default_factory=list)
