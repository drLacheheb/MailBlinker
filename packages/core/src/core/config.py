from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BASE_URL: str = "http://localhost:8000"
    DATABASE_URL: str = "sqlite+aiosqlite:///tracker.db"
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    API_KEY: Optional[str] = None
    RATE_LIMIT_ENABLED: bool = True
    LOG_FILE: str = "logs/app.log"
    HOST: str = "0.0.0.0"
    PORT: int = 8000


settings = Settings()
