from collections.abc import AsyncIterator

import asyncio
import psycopg
from fastapi import Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.db.session import get_db_session


def get_database_dsn(settings: Settings = Depends(get_settings)) -> str:
    return settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)


async def check_database(
    dsn: str = Depends(get_database_dsn),
) -> AsyncIterator[None]:
    def check() -> None:
        psycopg_dsn = dsn.replace("postgresql+psycopg://", "postgresql://", 1)
        with psycopg.connect(psycopg_dsn, connect_timeout=2) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

    try:
        await asyncio.to_thread(check)
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database dependency is unavailable",
        ) from exc
    yield


__all__ = ["check_database", "get_database_dsn", "get_db_session"]
