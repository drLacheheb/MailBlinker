from .create_email import CreateEmailDTO, CreateEmailResult, CreateEmailUseCase
from .delete_email import DeleteEmailUseCase
from .get_user_profile import GetUserProfileUseCase, UserProfileResult
from .list_emails import ListEmailsUseCase
from .record_open import RecordOpenDTO, RecordOpenResult, RecordOpenUseCase
from .update_notify_settings import UpdateNotifySettingsUseCase
from .update_user_preferences import UpdateUserPreferencesUseCase
from .upsert_user import UpsertUserDTO, UpsertUserUseCase

__all__ = [
    "CreateEmailDTO",
    "CreateEmailResult",
    "CreateEmailUseCase",
    "RecordOpenDTO",
    "RecordOpenResult",
    "RecordOpenUseCase",
    "ListEmailsUseCase",
    "DeleteEmailUseCase",
    "UpdateNotifySettingsUseCase",
    "UpsertUserDTO",
    "UpsertUserUseCase",
    "GetUserProfileUseCase",
    "UserProfileResult",
    "UpdateUserPreferencesUseCase",
]
