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

    # Outgoing email (password reset codes). Leave SMTP_HOST empty to disable sending.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "Duel Domain <no-reply@duel-domain.com>"
    SMTP_USE_TLS: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]


settings = Settings()
