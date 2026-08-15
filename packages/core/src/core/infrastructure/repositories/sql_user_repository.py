from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities import UserEntity
from ...domain.interfaces import UserRepositoryInterface
from ..db.models import UserModel


class SqlAlchemyUserRepository(UserRepositoryInterface):
    """SQLAlchemy implementation of the UserRepositoryInterface."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def upsert_user(
        self,
        telegram_chat_id: str,
        telegram_username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> UserEntity:
        now = datetime.now(timezone.utc)
        stmt = select(UserModel).where(UserModel.telegram_chat_id == telegram_chat_id)
        res = await self._session.execute(stmt)
        user = res.scalar_one_or_none()

        if user is None:
            user = UserModel(
                telegram_chat_id=telegram_chat_id,
                telegram_username=telegram_username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
                created_at=now,
                last_active_at=now,
            )
            self._session.add(user)
        else:
            if telegram_username is not None:
                user.telegram_username = telegram_username
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if language_code is not None:
                user.language_code = language_code
            user.last_active_at = now

        await self._session.commit()
        await self._session.refresh(user)
        return user.to_entity()

    async def get_by_telegram_chat_id(self, telegram_chat_id: str) -> Optional[UserEntity]:
        stmt = select(UserModel).where(UserModel.telegram_chat_id == telegram_chat_id)
        res = await self._session.execute(stmt)
        user = res.scalar_one_or_none()
        return user.to_entity() if user else None

    async def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        res = await self._session.execute(stmt)
        user = res.scalar_one_or_none()
        return user.to_entity() if user else None

    async def update_preferences(
        self,
        user_id: int,
        default_notify_limit: Optional[int] = None,
        update_notify_limit: bool = False,
        default_notify_forwarding: Optional[bool] = None,
        timezone: Optional[str] = None,
    ) -> Optional[UserEntity]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        res = await self._session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            return None

        if update_notify_limit:
            user.default_notify_limit = default_notify_limit
        if default_notify_forwarding is not None:
            user.default_notify_forwarding = default_notify_forwarding
        if timezone is not None:
            user.timezone = timezone

        await self._session.commit()
        await self._session.refresh(user)
        return user.to_entity()

    async def list_users(self, limit: int = 100, offset: int = 0) -> List[UserEntity]:
        stmt = (
            select(UserModel).order_by(desc(UserModel.last_active_at)).limit(limit).offset(offset)
        )
        res = await self._session.execute(stmt)
        models = res.scalars().all()
        return [m.to_entity() for m in models]
