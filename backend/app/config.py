"""
Central settings object. Everything sensitive is pulled from the .env
file (never hard-coded) via pydantic-settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    ADMIN_EMAIL: str
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    ADMIN_FIRST_NAME: str = "Admin"
    ADMIN_LAST_NAME: str = "User"

    SITE_NAME: str = "Nidhas Talks"
    SITE_URL: str = "http://localhost:8000"
    FRONTEND_ORIGIN: str = "http://localhost:8000"
    ENV: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
