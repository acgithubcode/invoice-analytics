from urllib.parse import urlparse

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings


def _safe_database_url() -> str:
    parsed = urlparse(settings.database_url)
    username = parsed.username or ""
    password_marker = ":***" if parsed.password else ""
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    database = parsed.path or ""
    return f"{parsed.scheme}://{username}{password_marker}@{host}{port}{database}"


def main() -> None:
    print(f"Database URL: {_safe_database_url()}")
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        print("Database connection failed.")
        print(str(exc))
        raise SystemExit(1) from exc

    print("Database connection successful.")


if __name__ == "__main__":
    main()
