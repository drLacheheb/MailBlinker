from typing import List

from ..domain.entities import TrackedEmailEntity
from ..domain.interfaces import EmailRepositoryInterface


class ListEmailsUseCase:
    def __init__(self, repository: EmailRepositoryInterface):
        self._repository = repository

    async def execute(self, limit: int = 100) -> List[TrackedEmailEntity]:
        return await self._repository.list_all(limit=limit)
