from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def get_database_url() -> str:
    return get_settings().database_url


engine = create_engine(get_database_url(), pool_pre_ping=True)
session_factory = sessionmaker(engine, expire_on_commit=False)


def get_db_session() -> Iterator[Session]:
    with session_factory() as session:
        yield session
