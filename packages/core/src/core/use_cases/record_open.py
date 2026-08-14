from dataclasses import dataclass
from datetime import datetime
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
        )

        if not inspection.is_valid_open or not inspection.event:
            return RecordOpenResult(
                email=email,
                inspection=inspection,
                is_recorded=False,
            )

        updated_email = await self._repository.record_open_event(dto.token, inspection.event)

        if self._notifier and updated_email:
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
