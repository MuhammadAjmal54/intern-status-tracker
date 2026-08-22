import os
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.exc import OperationalError

load_dotenv()


def _build_database_url() -> str:
    user = os.getenv("POSTGRES_USER", "intern_user")
    password = os.getenv("POSTGRES_PASSWORD", "intern_password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "intern_tracker")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


DATABASE_URL = _build_database_url()

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def wait_for_db(retries: int = 10, delay: int = 3) -> None:
    """Retry connecting to the database until it's ready (needed in Docker)."""
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database connection established.")
            return
        except OperationalError as exc:
            print(
                f"Database not ready (attempt {attempt}/{retries}): {exc}. "
                f"Retrying in {delay}s…"
            )
            time.sleep(delay)
    raise RuntimeError("Could not connect to the database after multiple retries.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()