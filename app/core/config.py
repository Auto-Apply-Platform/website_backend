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
    admin_username: str | None = None
    admin_password: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()
