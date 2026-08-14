from core import (
    CreateEmailUseCase,
    DeleteEmailUseCase,
    HttpGeoIpResolver,
    ListEmailsUseCase,
    RecordOpenUseCase,
    SqlAlchemyEmailRepository,
    TelegramNotificationService,
    get_db,
)
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


def get_email_repository(
    session: AsyncSession = Depends(get_db),
) -> SqlAlchemyEmailRepository:
    return SqlAlchemyEmailRepository(session)


def get_notification_service() -> TelegramNotificationService:
    return TelegramNotificationService()


def get_geoip_resolver() -> HttpGeoIpResolver:
    return HttpGeoIpResolver()


def get_create_email_use_case(
    repo: SqlAlchemyEmailRepository = Depends(get_email_repository),
) -> CreateEmailUseCase:
    return CreateEmailUseCase(repository=repo)


def get_record_open_use_case(
    repo: SqlAlchemyEmailRepository = Depends(get_email_repository),
    notifier: TelegramNotificationService = Depends(get_notification_service),
    geoip: HttpGeoIpResolver = Depends(get_geoip_resolver),
) -> RecordOpenUseCase:
    return RecordOpenUseCase(repository=repo, notifier=notifier, geoip_resolver=geoip)


def get_list_emails_use_case(
    repo: SqlAlchemyEmailRepository = Depends(get_email_repository),
) -> ListEmailsUseCase:
    return ListEmailsUseCase(repository=repo)


def get_delete_email_use_case(
    repo: SqlAlchemyEmailRepository = Depends(get_email_repository),
) -> DeleteEmailUseCase:
    return DeleteEmailUseCase(repository=repo)
