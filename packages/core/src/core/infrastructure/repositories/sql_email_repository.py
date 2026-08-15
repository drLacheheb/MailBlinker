from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.entities import OpenEventEntity, TrackedEmailEntity
from ...domain.interfaces import EmailRepositoryInterface
from ..db.models import OpenEventModel, TrackedEmailModel


class SqlAlchemyEmailRepository(EmailRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, email: TrackedEmailEntity) -> TrackedEmailEntity:
        model = TrackedEmailModel(
            token=email.token,
            title=email.title,
            recipient_email=email.recipient_email,
            recipient_name=email.recipient_name,
            subject=email.subject,
            telegram_chat_id=email.telegram_chat_id,
            created_at=email.created_at,
            first_opened_at=email.first_opened_at,
            last_opened_at=email.last_opened_at,
            open_count=email.open_count,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model.to_entity()

    async def get_by_token(self, token: str) -> Optional[TrackedEmailEntity]:
        stmt = (
            select(TrackedEmailModel)
            .options(selectinload(TrackedEmailModel.events))
            .where(TrackedEmailModel.token == token)
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_id(self, email_id: int) -> Optional[TrackedEmailEntity]:
        stmt = (
            select(TrackedEmailModel)
            .options(selectinload(TrackedEmailModel.events))
            .where(TrackedEmailModel.id == email_id)
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list_all(
        self, limit: int = 100, telegram_chat_id: Optional[str] = None
    ) -> List[TrackedEmailEntity]:
        stmt = (
            select(TrackedEmailModel)
            .options(selectinload(TrackedEmailModel.events))
            .order_by(desc(TrackedEmailModel.created_at))
        )
        if telegram_chat_id is not None:
            stmt = stmt.where(TrackedEmailModel.telegram_chat_id == telegram_chat_id)
        stmt = stmt.limit(limit)

        res = await self._session.execute(stmt)
        models = res.scalars().all()
        return [m.to_entity() for m in models]

    async def delete(self, email_id: int) -> bool:
        stmt = select(TrackedEmailModel).where(TrackedEmailModel.id == email_id)
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return False
        await self._session.delete(model)
        await self._session.commit()
        return True

    async def record_open_event(
        self,
        token: str,
        event: OpenEventEntity,
    ) -> Optional[TrackedEmailEntity]:
        stmt = (
            select(TrackedEmailModel)
            .options(selectinload(TrackedEmailModel.events))
            .where(TrackedEmailModel.token == token)
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None

        event_model = OpenEventModel(
            email_id=model.id,
            timestamp=event.timestamp,
            ip_address=event.ip_address,
            country=event.country,
            region=event.region,
            city=event.city,
            isp=event.isp,
            device_model=event.device_model,
            os_name=event.os_name,
            browser_name=event.browser_name,
            language=event.language,
            user_agent=event.user_agent,
            elapsed_seconds=event.elapsed_seconds,
        )
        self._session.add(event_model)

        model.open_count += 1
        if model.first_opened_at is None:
            model.first_opened_at = event.timestamp
        model.last_opened_at = event.timestamp

        await self._session.commit()
        await self._session.refresh(model)
        return model.to_entity()
