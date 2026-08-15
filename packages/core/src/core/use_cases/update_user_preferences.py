from typing import Optional

from ..domain.entities import UserEntity
from ..domain.interfaces import UserRepositoryInterface


class UpdateUserPreferencesUseCase:
    """Use case to configure account-level default alert limits, forwarding policy, and timezone."""

    def __init__(self, repository: UserRepositoryInterface):
        self._repository = repository

    async def execute(
        self,
        user_id: int,
        default_notify_limit: Optional[int] = None,
        update_notify_limit: bool = False,
        default_notify_forwarding: Optional[bool] = None,
        timezone: Optional[str] = None,
    ) -> Optional[UserEntity]:
        if update_notify_limit and default_notify_limit is not None and default_notify_limit < 0:
            raise ValueError("default_notify_limit must be a non-negative integer or None")

        return await self._repository.update_preferences(
            user_id=user_id,
            default_notify_limit=default_notify_limit,
            update_notify_limit=update_notify_limit,
            default_notify_forwarding=default_notify_forwarding,
            timezone=timezone,
        )
