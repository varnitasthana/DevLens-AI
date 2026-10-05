from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_repository_crud_against_postgresql() -> None:
    source_url = f"https://github.com/devlens/{uuid4().hex}.git"
    updated_url = f"https://github.com/devlens/{uuid4().hex}.git"
    duplicate_url = f"https://github.com/devlens/{uuid4().hex}.git"
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

    update_response = client.patch(
        f"/api/v1/repositories/{repository_id}",
        json={"name": "Updated DevLens Repository", "description": None},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated DevLens Repository"
    assert update_response.json()["description"] is None

    duplicate_source_response = client.patch(
        f"/api/v1/repositories/{repository_id}",
        json={"source_url": updated_url},
    )
    assert duplicate_source_response.status_code == 200

    second_repository = client.post(
        "/api/v1/repositories",
        json={**payload, "source_url": duplicate_url},
    )
    assert second_repository.status_code == 201
    conflict_response = client.patch(
        f"/api/v1/repositories/{second_repository.json()['id']}",
        json={"source_url": updated_url},
    )
    assert conflict_response.status_code == 409

    invalid_update_response = client.patch(
        f"/api/v1/repositories/{repository_id}",
        json={"unknown_field": "rejected"},
    )
    assert invalid_update_response.status_code == 422

    missing_update_response = client.patch(
        f"/api/v1/repositories/{uuid4()}",
        json={"name": "Missing"},
    )
    assert missing_update_response.status_code == 404

    duplicate_response = client.post(
        "/api/v1/repositories",
        json={**payload, "source_url": duplicate_url},
    )
    assert duplicate_response.status_code == 409

    delete_response = client.delete(f"/api/v1/repositories/{repository_id}")
    assert delete_response.status_code == 204
    assert client.delete(f"/api/v1/repositories/{second_repository.json()['id']}").status_code == 204

    missing_response = client.get(f"/api/v1/repositories/{repository_id}")
    assert missing_response.status_code == 404
