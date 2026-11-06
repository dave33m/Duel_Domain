from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # No default: a missing key must stop the app rather than fall back to a public value.
    SECRET_KEY: str = Field(min_length=32)
    DEBUG: bool = False
    ALLOWED_HOSTS: str = ""
    # Comma-separated browser origins allowed to call the API, or "*" for any.
    CORS_ORIGINS: str = "*"
    DATABASE_URL: str = "sqlite+aiosqlite:///./db.sqlite3"

    # Email is sent with fastapi-mail through Resend's SMTP relay; the Resend API key is the
    # SMTP password. Leave RESEND_API_KEY empty to disable sending (emails are only logged).
    RESEND_API_KEY: str = ""
    MAIL_SERVER: str = "smtp.resend.com"
    MAIL_PORT: int = 587
    MAIL_FROM: str = "duel@duel-domain.com"
    MAIL_FROM_NAME: str = "Duel Domain"
    MAIL_REPLY_TO: str = "support@duel-domain.com"
    # Comma-separated addresses told about every new signup; empty to disable.
    ADMIN_NOTIFY_EMAILS: str = ""
    # Used for links inside emails.
    FRONTEND_URL: str = "https://duel-domain.com"

    # Uploaded files (game banners) and the per-file size limit.
    UPLOAD_DIR: str = "uploads"
    MAX_BANNER_BYTES: int = 5 * 1024 * 1024

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def admin_notify_emails_list(self) -> list[str]:
        return [e.strip() for e in self.ADMIN_NOTIFY_EMAILS.split(",") if e.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]


settings = Settings()
