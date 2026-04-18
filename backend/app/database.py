from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import BACKEND_DIR, get_settings


class Base(DeclarativeBase):
    pass


def _connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _resolve_database_url(database_url: str) -> str:
    if not database_url.startswith("sqlite:///"):
        return database_url

    raw_path = database_url[len("sqlite:///"):]
    if not raw_path or raw_path == ":memory:":
        return database_url

    path = Path(raw_path)
    if path.is_absolute():
        return database_url

    absolute_path = (BACKEND_DIR / path).resolve().as_posix()
    return f"sqlite:///{absolute_path}"


@lru_cache
def get_engine(database_url: str | None = None):
    resolved_url = _resolve_database_url(database_url or get_settings().database_url)
    return create_engine(
        resolved_url,
        future=True,
        connect_args=_connect_args(resolved_url),
    )


@lru_cache
def get_session_factory(database_url: str | None = None):
    return sessionmaker(
        bind=get_engine(database_url),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    from app.models import load_all_models

    load_all_models()
    Base.metadata.create_all(bind=get_engine())


def reset_database_cache() -> None:
    get_session_factory.cache_clear()
    get_engine.cache_clear()

