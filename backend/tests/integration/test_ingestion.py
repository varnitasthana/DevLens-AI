import io
import zipfile
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def zip_bytes(files: dict[str, bytes]) -> io.BytesIO:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    stream.seek(0)
    return stream


def test_repository_zip_ingestion_persists_file_metadata() -> None:
    repository = client.post(
        "/api/v1/repositories",
        json={
            "name": "Ingestion Test",
            "source_url": f"https://github.com/devlens/{uuid4().hex}.git",
        },
    )
    assert repository.status_code == 201
    repository_id = repository.json()["id"]

    response = client.post(
        f"/api/v1/repositories/{repository_id}/ingest",
        files={
            "upload": (
                "repository.zip",
                zip_bytes(
                    {
                        "src/main.py": b"print('safe')",
                        "README.md": b"# test",
                        "node_modules/ignored.js": b"ignored",
                        "binary.py": b"\x00not source",
                    }
                ),
                "application/zip",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["file_count"] == 2
    assert response.json()["files"] == ["README.md", "src/main.py"]

    assert client.delete(f"/api/v1/repositories/{repository_id}").status_code == 204
