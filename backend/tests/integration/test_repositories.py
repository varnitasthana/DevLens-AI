from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_repository_crud_against_postgresql() -> None:
    source_url = f"https://github.com/devlens/{uuid4().hex}.git"
    payload = {
        "name": "DevLens Integration Test",
        "source_url": source_url,
        "default_branch": "main",
        "description": "Created by the PostgreSQL integration test",
    }

    create_response = client.post("/api/v1/repositories", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    repository_id = created["id"]
    assert created["source_url"] == source_url

    list_response = client.get("/api/v1/repositories")
    assert list_response.status_code == 200
    assert any(item["id"] == repository_id for item in list_response.json())

    get_response = client.get(f"/api/v1/repositories/{repository_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == payload["name"]

    duplicate_response = client.post("/api/v1/repositories", json=payload)
    assert duplicate_response.status_code == 409

    delete_response = client.delete(f"/api/v1/repositories/{repository_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/repositories/{repository_id}")
    assert missing_response.status_code == 404
