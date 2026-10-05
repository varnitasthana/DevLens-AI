from collections.abc import Sequence
import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.errors import ErrorBody, ErrorResponse

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: Sequence[dict[str, Any]] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details=list(details) if details else None,
            request_id=_request_id(request),
        )
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(exclude_none=True))


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return await unhandled_exception_handler(request, exc)
    return _error_response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details=exc.errors(),
    )


async def http_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    if not isinstance(exc, (StarletteHTTPException, HTTPException)):
        return await unhandled_exception_handler(request, exc)
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return _error_response(
        request,
        status_code=exc.status_code,
        code="HTTP_ERROR",
        message=message,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_exception",
        extra={"request_id": _request_id(request)},
        exc_info=exc,
    )
    return _error_response(
        request,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
    )
