from typing import List, Optional, Protocol

from .entities import OpenEventEntity, TrackedEmailEntity


class EmailRepositoryInterface(Protocol):
    async def create(self, email: TrackedEmailEntity) -> TrackedEmailEntity: ...
    async def get_by_token(self, token: str) -> Optional[TrackedEmailEntity]: ...
    async def get_by_id(self, email_id: int) -> Optional[TrackedEmailEntity]: ...
    async def list_all(
        self, limit: int = 100, telegram_chat_id: Optional[str] = None
    ) -> List[TrackedEmailEntity]: ...
    async def delete(self, email_id: int) -> bool: ...
    async def record_open_event(
        self,
        token: str,
        event: OpenEventEntity,
    ) -> Optional[TrackedEmailEntity]: ...


class NotificationServiceInterface(Protocol):
    async def send_open_alert(
        self,
        email: TrackedEmailEntity,
        event: OpenEventEntity,
        device: str,
        forwarding_note: Optional[str] = None,
    ) -> None: ...


class GeoIpResolverInterface(Protocol):
    async def resolve(
        self, ip: Optional[str]
    ) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]: ...
