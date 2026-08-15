from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ...domain.entities import (
    OpenEventEntity,
    TrackedEmailEntity,
)


class Base(DeclarativeBase):
    pass


class TrackedEmailModel(Base):
    __tablename__ = "tracked_emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    first_opened_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_opened_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    open_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    events: Mapped[List["OpenEventModel"]] = relationship(
        "OpenEventModel",
        back_populates="email",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(OpenEventModel.timestamp)",
    )

    def to_entity(self) -> TrackedEmailEntity:
        events_entities = []
        if "events" in self.__dict__ and self.events:
            events_entities = [e.to_entity() for e in self.events]

        return TrackedEmailEntity(
            id=self.id,
            token=self.token,
            title=self.title,
            recipient_email=self.recipient_email,
            recipient_name=self.recipient_name,
            subject=self.subject,
            telegram_chat_id=self.telegram_chat_id,
            created_at=self.created_at,
            first_opened_at=self.first_opened_at,
            last_opened_at=self.last_opened_at,
            open_count=self.open_count,
            events=events_entities,
        )


class OpenEventModel(Base):
    __tablename__ = "open_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tracked_emails.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    isp: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    device_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    os_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    browser_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    elapsed_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    email: Mapped["TrackedEmailModel"] = relationship("TrackedEmailModel", back_populates="events")

    def to_entity(self) -> OpenEventEntity:
        return OpenEventEntity(
            id=self.id,
            email_id=self.email_id,
            timestamp=self.timestamp,
            ip_address=self.ip_address,
            country=self.country,
            region=self.region,
            city=self.city,
            isp=self.isp,
            device_model=self.device_model,
            os_name=self.os_name,
            browser_name=self.browser_name,
            language=self.language,
            user_agent=self.user_agent,
            elapsed_seconds=self.elapsed_seconds,
        )
