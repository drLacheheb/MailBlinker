from typing import List, Optional, Protocol

from .entities import OpenEventEntity, TrackedEmailEntity, UserEntity


class UserRepositoryInterface(Protocol):
    async def upsert_user(
        self,
        telegram_chat_id: str,
        telegram_username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> UserEntity: ...

    async def get_by_telegram_chat_id(self, telegram_chat_id: str) -> Optional[UserEntity]: ...

    async def get_by_id(self, user_id: int) -> Optional[UserEntity]: ...

    async def update_preferences(
        self,
        user_id: int,
        default_notify_limit: Optional[int] = None,
        update_notify_limit: bool = False,
        default_notify_forwarding: Optional[bool] = None,
        timezone: Optional[str] = None,
    ) -> Optional[UserEntity]: ...

    async def list_users(self, limit: int = 100, offset: int = 0) -> List[UserEntity]: ...


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
    async def update_notify_settings(
        self,
        email_id: int,
        limit: Optional[int] = None,
        update_limit: bool = False,
        notify_forwarding: Optional[bool] = None,
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
