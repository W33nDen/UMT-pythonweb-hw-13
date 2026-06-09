from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/contacts_db"
    secret_key: str = "91f744e8de81e813959c5d8091873111ce51792a7a40b9042cbfbdcdfa0e0b3c"
    algorithm: str = "HS256"

    # SMTP Settings
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_port: int = 587
    mail_server: str = ""
    mail_from_name: str = "ContactsRESTAPI"

    # Cloudinary Settings
    cloudinary_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    # Redis Settings
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

