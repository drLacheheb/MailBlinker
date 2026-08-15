from typing import List, Optional

from ..domain.entities import TrackedEmailEntity
from ..domain.interfaces import EmailRepositoryInterface


class ListEmailsUseCase:
    def __init__(self, repository: EmailRepositoryInterface):
        self._repository = repository

    async def execute(
        self, limit: int = 100, telegram_chat_id: Optional[str] = None
    ) -> List[TrackedEmailEntity]:
        return await self._repository.list_all(limit=limit, telegram_chat_id=telegram_chat_id)
