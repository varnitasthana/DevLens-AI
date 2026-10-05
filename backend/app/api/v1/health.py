from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.dependencies import check_database
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(
    settings: Settings = Depends(get_settings),
    _: None = Depends(check_database),
) -> ReadinessResponse:
    return ReadinessResponse(
        status="ready",
        service=settings.app_name,
        dependencies={"database": "ok"},
    )
