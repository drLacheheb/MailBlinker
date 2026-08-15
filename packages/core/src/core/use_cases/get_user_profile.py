from dataclasses import dataclass
from typing import Optional

from ..domain.entities import UserEntity
from ..domain.interfaces import EmailRepositoryInterface, UserRepositoryInterface


@dataclass(frozen=True)
class UserProfileResult:
    user: UserEntity
    total_emails: int
    total_opens: int


class GetUserProfileUseCase:
    """Use case to fetch a user profile along with aggregate tracker stats."""

    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        email_repository: EmailRepositoryInterface,
    ):
        self._user_repository = user_repository
        self._email_repository = email_repository

    async def execute(self, telegram_chat_id: str) -> Optional[UserProfileResult]:
        user = await self._user_repository.get_by_telegram_chat_id(telegram_chat_id)
        if not user:
            return None

        emails = await self._email_repository.list_all(
            limit=1000, telegram_chat_id=telegram_chat_id
        )
        total_emails = len(emails)
        total_opens = sum(e.open_count for e in emails)

        return UserProfileResult(
            user=user,
            total_emails=total_emails,
            total_opens=total_opens,
        )
