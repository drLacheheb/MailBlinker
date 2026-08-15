from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
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
    UserEntity,
)


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_chat_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    telegram_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    default_notify_limit: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )
    default_notify_forwarding: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    emails: Mapped[List["TrackedEmailModel"]] = relationship(
        "TrackedEmailModel",
        back_populates="user",
        lazy="selectin",
        order_by="desc(TrackedEmailModel.created_at)",
    )

    def to_entity(self) -> UserEntity:
        return UserEntity(
            id=self.id,
            telegram_chat_id=self.telegram_chat_id,
            telegram_username=self.telegram_username,
            first_name=self.first_name,
            last_name=self.last_name,
            language_code=self.language_code,
            default_notify_limit=self.default_notify_limit,
            default_notify_forwarding=self.default_notify_forwarding,
            timezone=self.timezone,
            is_active=self.is_active,
            created_at=self.created_at,
            last_active_at=self.last_active_at,
        )


class TrackedEmailModel(Base):
    __tablename__ = "tracked_emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

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
    notify_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    notify_forwarding: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    user: Mapped[Optional["UserModel"]] = relationship("UserModel", back_populates="emails")

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
            user_id=self.user_id,
            created_at=self.created_at,
            first_opened_at=self.first_opened_at,
            last_opened_at=self.last_opened_at,
            open_count=self.open_count,
            notify_limit=self.notify_limit,
            notify_forwarding=self.notify_forwarding,
            expires_at=self.expires_at,
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
