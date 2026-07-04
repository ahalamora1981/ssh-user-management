from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/users.db"

    # JWT
    SECRET_KEY: str = "change-this-to-a-random-64-char-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    # SMTP
    SMTP_SERVER: str = "smtp.163.com"
    SMTP_PORT: int = 465
    SMTP_USERNAME: str = "taojundev@163.com"
    SMTP_PASSWORD: str = ""
    SENDER_EMAIL: str = "taojundev@163.com"
    SENDER_NAME: str = "SSH User Management"

    # Server
    SERVER_IP: str = "localhost"
    KEYS_DIR: str = "./keys"

    # Admin
    ADMIN_EMAILS: str = "taojundev@163.com"

    @property
    def admin_emails_list(self) -> List[str]:
        return [e.strip() for e in self.ADMIN_EMAILS.split(",") if e.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
