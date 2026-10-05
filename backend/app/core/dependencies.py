from collections.abc import AsyncIterator

import psycopg
from fastapi import Depends, HTTPException, status

from app.core.config import Settings, get_settings


def get_database_dsn(settings: Settings = Depends(get_settings)) -> str:
    return settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)


async def check_database(
    dsn: str = Depends(get_database_dsn),
) -> AsyncIterator[None]:
    try:
        async with await psycopg.AsyncConnection.connect(
            dsn, connect_timeout=2
        ) as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT 1")
                await cursor.fetchone()
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database dependency is unavailable",
        ) from exc
    yield
