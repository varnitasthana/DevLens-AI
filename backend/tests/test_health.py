from fastapi.testclient import TestClient

from app.api.v1.health import check_database
from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_application_status() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "DevLens API",
        "environment": "development",
    }


def test_health_endpoint_returns_request_id() -> None:
    response = client.get("/api/v1/health", headers={"x-request-id": "test-request"})

    assert response.headers["x-request-id"] == "test-request"


def test_readiness_endpoint_reports_database_ready() -> None:
    async def database_is_ready():
        yield

    app.dependency_overrides[check_database] = database_is_ready
    try:
        response = client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["dependencies"] == {"database": "ok"}


def test_readiness_endpoint_reports_dependency_failure() -> None:
    async def database_is_unavailable():
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail="Database dependency is unavailable",
        )
        yield

    app.dependency_overrides[check_database] = database_is_unavailable
    try:
        response = client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "HTTP_ERROR"
    assert response.json()["error"]["message"] == "Database dependency is unavailable"
