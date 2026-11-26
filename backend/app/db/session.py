from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    with sessionmaker(bind=get_engine(), expire_on_commit=False)() as session:
        yield session


SessionFactory = Callable[[], AbstractContextManager[Session]]


def get_session_factory() -> SessionFactory:
    """For work that outlives the request (background jobs): each call opens its own session."""
    return sessionmaker(bind=get_engine(), expire_on_commit=False)
