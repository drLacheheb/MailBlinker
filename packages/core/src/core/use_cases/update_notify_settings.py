from typing import Optional

from ..domain.entities import TrackedEmailEntity
from ..domain.interfaces import EmailRepositoryInterface


class UpdateNotifySettingsUseCase:
    """Use case to configure notification limit and forwarding alert settings per email."""

    def __init__(self, repository: EmailRepositoryInterface):
        self._repository = repository

    async def execute(
        self,
        email_id: int,
        limit: Optional[int] = None,
        update_limit: bool = False,
        notify_forwarding: Optional[bool] = None,
    ) -> Optional[TrackedEmailEntity]:
        if update_limit and limit is not None and limit < 0:
            raise ValueError("notify_limit must be a non-negative integer or None")

        return await self._repository.update_notify_settings(
            email_id=email_id,
            limit=limit,
            update_limit=update_limit,
            notify_forwarding=notify_forwarding,
        )
