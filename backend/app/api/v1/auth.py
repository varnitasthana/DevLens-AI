import asyncio
from collections.abc import Iterator
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth import AuthService, create_token
router = APIRouter(prefix="/auth", tags=["auth"])
def service(session: Session = Depends(get_db_session)) -> Iterator[AuthService]:
    yield AuthService(session)
@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, svc: AuthService = Depends(service), settings: Settings = Depends(get_settings)) -> TokenResponse:
    try:
        user = await asyncio.to_thread(svc.register, str(data.email), data.password)
    except IntegrityError as exc:
        svc.session.rollback()
        raise HTTPException(status_code=409, detail="Email is already registered") from exc
    return TokenResponse(access_token=create_token(user.id, settings.auth_secret_key, settings.auth_token_expire_minutes), user=UserResponse.model_validate(user))
@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, svc: AuthService = Depends(service), settings: Settings = Depends(get_settings)) -> TokenResponse:
    user = await asyncio.to_thread(svc.authenticate, str(data.email), data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    return TokenResponse(access_token=create_token(user.id, settings.auth_secret_key, settings.auth_token_expire_minutes), user=UserResponse.model_validate(user))
