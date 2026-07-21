from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    SECRET_KEY: str = "django-insecure-d^+-0+-xx$0*b1_5^!)5+vd1ey(+$)ue=ve+h#t!9_y73bx70-"
    DEBUG: bool = True
    ALLOWED_HOSTS: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./db.sqlite3"

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]


settings = Settings()
