from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = ""
    webapp_url: str = "http://127.0.0.1:8000"

    # Render PostgreSQL: set DATABASE_URL. For local launch SQLite is used as fallback.
    database_url: str = ""
    database_path: str = "cinema.db"

    app_secret: str = "change-me"
    telegram_webhook_secret: str = "change-me-webhook"
    webhook_enabled: bool = True

    admin_user_ids: str = ""

    # Optional metadata provider. AniList works without a key; TMDB expands movie/TV search.
    anilist_enabled: bool = True
    tmdb_bearer_token: str = ""

    # Optional authorized stream resolver API.
    source_api_url: str = ""
    source_api_name: str = "My Source"
    source_api_token: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def admins(self) -> set[int]:
        out: set[int] = set()
        for x in self.admin_user_ids.split(","):
            x = x.strip()
            if x.isdigit():
                out.add(int(x))
        return out

    @property
    def effective_database_url(self) -> str:
        url = self.database_url.strip()
        if url:
            # Render commonly exposes postgresql://. Force SQLAlchemy to use psycopg v3.
            if url.startswith("postgresql://"):
                return "postgresql+psycopg://" + url.removeprefix("postgresql://")
            if url.startswith("postgres://"):
                return "postgresql+psycopg://" + url.removeprefix("postgres://")
            return url
        return f"sqlite:///{self.database_path}"

    @property
    def webhook_url(self) -> str:
        return self.webapp_url.rstrip("/") + "/telegram/webhook"


settings = Settings()
