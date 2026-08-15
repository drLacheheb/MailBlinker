from dataclasses import dataclass
from typing import Optional

from ..domain.entities import UserEntity
from ..domain.interfaces import UserRepositoryInterface


@dataclass(frozen=True)
class UpsertUserDTO:
    telegram_chat_id: str
    telegram_username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None


class UpsertUserUseCase:
    """Use case to ensure a user record exists and update activity/profile details."""

    def __init__(self, repository: UserRepositoryInterface):
        self._repository = repository

    async def execute(self, dto: UpsertUserDTO) -> UserEntity:
        return await self._repository.upsert_user(
            telegram_chat_id=dto.telegram_chat_id,
            telegram_username=dto.telegram_username,
            first_name=dto.first_name,
            last_name=dto.last_name,
            language_code=dto.language_code,
        )
