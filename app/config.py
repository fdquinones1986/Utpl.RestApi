# config.py
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # JWT Token Related
    secret_key: str
    refresh_secret_key: str
    algorithm: str
    timeout: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    EMAIL_PASSWORD: str
    EMAIL_SENDER: str
    EMAIL_SMTP_SERVER: str
    EMAIL_SMTP_PORT: int
    # internal env
    adminapikey: str
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str

    class Config:
        env_file = Path(Path(__file__).resolve().parent) / ".env"
        print(f'environment created - {Path(Path(__file__).resolve().name)}')


setting = Settings()
