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
    TELEGRAM_BOT_MODE: str = "auto"  # "auto", "webhook", or "polling"
    TELEGRAM_WEBHOOK_PATH: str = "/api/webhook/telegram"
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None
    API_KEY: Optional[str] = None
    RATE_LIMIT_ENABLED: bool = True
    LOG_FILE: str = "logs/app.log"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    @property
    def is_webhook_mode(self) -> bool:
        if not self.TELEGRAM_BOT_TOKEN:
            return False
        mode = self.TELEGRAM_BOT_MODE.lower()
        if mode == "webhook":
            return True
        if mode == "polling":
            return False
        # In auto mode, use webhook if public HTTPS URL is configured
        return self.BASE_URL.startswith("https://")


settings = Settings()
