from collections.abc import AsyncIterator

import asyncio
import psycopg
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from app.models.user import User

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


security = HTTPBearer(auto_error=False)
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session=Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> User:
    from app.services.auth import decode_token
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    user_id = decode_token(credentials.credentials, settings.auth_secret_key)
    user = session.scalar(select(User).where(User.id == user_id)) if user_id else None
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    return user
__all__ = ["check_database", "get_database_dsn", "get_db_session", "get_current_user"]
