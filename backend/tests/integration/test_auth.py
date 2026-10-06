from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def register(email: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register", json={"email": email, "password": "correct-horse-battery"}
    )
    assert response.status_code == 201
    return response.json()


def test_protected_repository_requires_authentication() -> None:
    assert client.get("/api/v1/repositories").status_code == 401


def test_authentication_and_repository_ownership() -> None:
    first = register(f"{uuid4().hex}@example.com")
    second = register(f"{uuid4().hex}@example.com")
    first_headers = {"Authorization": f"Bearer {first['access_token']}"}
    second_headers = {"Authorization": f"Bearer {second['access_token']}"}
    created = client.post(
        "/api/v1/repositories",
        headers=first_headers,
        json={"name": "private", "source_url": f"https://example.com/{uuid4().hex}"},
    )
    assert created.status_code == 201
    repository_id = created.json()["id"]
    assert client.get("/api/v1/repositories", headers=second_headers).json() == []
    assert client.get(f"/api/v1/repositories/{repository_id}", headers=second_headers).status_code == 404
    assert client.get(f"/api/v1/repositories/{repository_id}", headers=first_headers).status_code == 200
