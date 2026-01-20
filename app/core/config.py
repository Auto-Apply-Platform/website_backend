from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "website_backend"
    mongodb_uri: str = "mongodb://mongo:27017"
    mongodb_db: str = "website_backend"
    uploads_dir: str = "uploads"
    auth_jwt_secret: str = "change_me"
    auth_jwt_alg: str = "HS256"
    access_token_expires_seconds: int = 3600
    login_token_ttl_seconds: int = 300
    telegram_bot_username: str = ""
    telegram_bot_secret: str = ""
    tg_whitelist: str = ""
    admin_username: str | None = None
    admin_password: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def tg_whitelist_set(self) -> set[int]:
        if not self.tg_whitelist:
            return set()
        result: set[int] = set()
        for item in self.tg_whitelist.split(","):
            item = item.strip()
            if not item:
                continue
            try:
                result.add(int(item))
            except ValueError:
                continue
        return result


settings = Settings()
