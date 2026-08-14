from datetime import datetime, timezone

import pytest
from core import (
    AsyncSessionLocal,
    CreateEmailDTO,
    CreateEmailUseCase,
    DeleteEmailUseCase,
    ListEmailsUseCase,
    RecordOpenDTO,
    RecordOpenUseCase,
    SqlAlchemyEmailRepository,
    init_db,
)


@pytest.mark.asyncio
async def test_clean_architecture_use_cases():
    await init_db()

    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyEmailRepository(session)

        create_uc = CreateEmailUseCase(repository=repo)
        dto = CreateEmailDTO(
            title="Clean Architecture Proposal",
            recipient_email="architect@example.com",
            recipient_name="Martin Fowler",
            body_text="Testing domain use cases decoupling.",
        )
        create_result = await create_uc.execute(dto)

        assert create_result.email.id is not None
        assert create_result.email.title == "Clean Architecture Proposal"
        assert create_result.email.recipient_email == "architect@example.com"
        assert create_result.pixel_url.endswith(f"/track/{create_result.email.token}.gif")
        assert "Martin Fowler" in create_result.formatted_html

        record_uc = RecordOpenUseCase(repository=repo)
        open_dto = RecordOpenDTO(
            token=create_result.email.token,
            open_time=datetime.now(timezone.utc),
            client_ip="127.0.0.1",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        )
        open_result = await record_uc.execute(open_dto)

        assert open_result.email is not None
        assert open_result.inspection is not None

        list_uc = ListEmailsUseCase(repository=repo)
        emails = await list_uc.execute()
        assert len(emails) >= 1
        assert any(e.token == create_result.email.token for e in emails)

        delete_uc = DeleteEmailUseCase(repository=repo)
        deleted = await delete_uc.execute(create_result.email.id)
        assert deleted is True

        not_found = await repo.get_by_id(create_result.email.id)
        assert not_found is None
