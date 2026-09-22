from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str = ""
    webapp_url: str = "http://127.0.0.1:8000"
    database_path: str = "cinema.db"
    app_secret: str = "change-me"
    admin_user_ids: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def admins(self) -> set[int]:
        out = set()
        for x in self.admin_user_ids.split(","):
            x = x.strip()
            if x.isdigit():
                out.add(int(x))
        return out

settings = Settings()
