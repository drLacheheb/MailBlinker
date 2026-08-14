from ..domain.interfaces import EmailRepositoryInterface


class DeleteEmailUseCase:
    def __init__(self, repository: EmailRepositoryInterface):
        self._repository = repository

    async def execute(self, email_id: int) -> bool:
        return await self._repository.delete(email_id)
