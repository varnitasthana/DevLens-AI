from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_invalid_method_returns_structured_error() -> None:
    response = client.post("/api/v1/health")

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "HTTP_ERROR"
    assert response.json()["error"]["request_id"]


def test_unknown_route_returns_structured_error() -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "HTTP_ERROR"
