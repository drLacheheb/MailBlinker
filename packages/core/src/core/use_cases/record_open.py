from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from ..domain.entities import TrackedEmailEntity
from ..domain.interfaces import (
    EmailRepositoryInterface,
    GeoIpResolverInterface,
    NotificationServiceInterface,
)
from ..telemetry.inspector import TelemetryInspectionResult, TelemetryInspector


@dataclass
class RecordOpenDTO:
    token: str
    open_time: datetime
    client_ip: Optional[str]
    user_agent: Optional[str]
    accept_language: Optional[str] = None
    purpose: Optional[str] = None
    client_hints: Optional[dict[str, str]] = None
    tls_version: Optional[str] = None


@dataclass
class RecordOpenResult:
    email: Optional[TrackedEmailEntity]
    inspection: Optional[TelemetryInspectionResult]
    is_recorded: bool


class RecordOpenUseCase:
    def __init__(
        self,
        repository: EmailRepositoryInterface,
        notifier: Optional[NotificationServiceInterface] = None,
        geoip_resolver: Optional[GeoIpResolverInterface] = None,
        inspector: Optional[TelemetryInspector] = None,
    ):
        self._repository = repository
        self._notifier = notifier
        self._geoip_resolver = geoip_resolver
        self._inspector = inspector or TelemetryInspector()

    async def execute(self, dto: RecordOpenDTO) -> RecordOpenResult:
        email = await self._repository.get_by_token(dto.token)
        if not email:
            return RecordOpenResult(email=None, inspection=None, is_recorded=False)

        # Check if email tracking token has expired
        if email.expires_at:
            exp = email.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            open_t = dto.open_time
            if open_t.tzinfo is None:
                open_t = open_t.replace(tzinfo=timezone.utc)
            if open_t > exp:
                return RecordOpenResult(email=email, inspection=None, is_recorded=False)

        geo_data = (
            await self._geoip_resolver.resolve(dto.client_ip)
            if self._geoip_resolver
            else (None, None, None, None)
        )

        inspection = self._inspector.inspect(
            email_id=email.id or 0,
            sent_at=email.created_at,
            open_time=dto.open_time,
            ip_address=dto.client_ip,
            user_agent=dto.user_agent,
            accept_language=dto.accept_language,
            past_events=email.events,
            geo_data=geo_data,
            purpose=dto.purpose,
            client_hints=dto.client_hints,
            tls_version=dto.tls_version,
        )

        if not inspection.is_valid_open or not inspection.event:
            return RecordOpenResult(
                email=email,
                inspection=inspection,
                is_recorded=False,
            )

        updated_email = await self._repository.record_open_event(dto.token, inspection.event)

        if self._notifier and updated_email:
            should_notify = True
            limit = updated_email.notify_limit

            if limit == 0:
                should_notify = False
            elif limit is not None and updated_email.open_count > limit:
                should_notify = False

            # Smart Forwarding Override: If muted/limited, but forwarded -> notify!
            is_forwarding = bool(inspection.forwarding_note)
            if not should_notify and updated_email.notify_forwarding and is_forwarding:
                should_notify = True

            if should_notify:
                await self._notifier.send_open_alert(
                    updated_email,
                    inspection.event,
                    device=inspection.device_summary,
                    forwarding_note=inspection.forwarding_note,
                )

        return RecordOpenResult(
            email=updated_email,
            inspection=inspection,
            is_recorded=True,
        )
