import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.health import router as health_router
from app.api.v1.analyses import router as analyses_router
from app.api.v1.test_generation import router as test_generation_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.github import router as github_router
from app.api.v1.pull_requests import router as pull_requests_router
from app.api.v1.auth import router as auth_router
from app.api.v1.repositories import router as repositories_router
from app.core.config import get_settings
from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import RedisRateLimitMiddleware

settings = get_settings()
configure_logging(settings.log_level)
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    RedisRateLimitMiddleware,
    redis_url=settings.redis_url,
    limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.include_router(health_router, prefix="/api/v1")
app.include_router(repositories_router, prefix="/api/v1")
app.include_router(analyses_router, prefix="/api/v1")
app.include_router(test_generation_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(github_router, prefix="/api/v1")
app.include_router(pull_requests_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

logger = logging.getLogger(__name__)
