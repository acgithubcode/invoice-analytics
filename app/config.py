import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    app_name: str = os.getenv("APP_NAME", "Invoice Ledger API")
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/invoice_ledger",
    )

    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]

    def validate(self) -> None:
        if self.app_env == "production" and self.jwt_secret_key == "change-this-secret-in-production":
            raise RuntimeError("JWT_SECRET_KEY must be changed in production.")


@lru_cache
def get_settings() -> Settings:
    loaded_settings = Settings()
    loaded_settings.validate()
    return loaded_settings


settings = get_settings()
