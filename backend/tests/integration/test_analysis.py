import io
import zipfile
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analysis_persists_static_findings() -> None:
    repository = client.post(
        "/api/v1/repositories",
        json={
            "name": "Analysis Test",
            "source_url": f"https://github.com/devlens/{uuid4().hex}.git",
        },
    )
    repository_id = repository.json()["id"]
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("bad.py", "value = eval(user_input)\n")
        archive.writestr("bad.js", "element.innerHTML = value;\n")
    stream.seek(0)

    response = client.post(
        f"/api/v1/repositories/{repository_id}/analyze",
        files={"upload": ("analysis.zip", stream, "application/zip")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert {finding["source"] for finding in body["findings"]} == {"static"}
    assert {finding["rule"] for finding in body["findings"]} == {
        "python.eval",
        "javascript.inner-html",
    }
    assert client.delete(f"/api/v1/repositories/{repository_id}").status_code == 204


def test_analysis_lifecycle_and_filtered_findings() -> None:
    repository = client.post(
        "/api/v1/repositories",
        json={
            "name": "Lifecycle Test",
            "source_url": f"https://github.com/devlens/{uuid4().hex}.git",
        },
    )
    repository_id = repository.json()["id"]
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("bad.py", "value = eval(user_input)\n")
        archive.writestr("debug.js", "console.log(value);\n")
    stream.seek(0)

    response = client.post(
        f"/api/v1/repositories/{repository_id}/analyses",
        files={"upload": ("analysis.zip", stream, "application/zip")},
    )
    assert response.status_code == 200
    analysis = response.json()
    assert analysis["status"] == "COMPLETED"
    assert analysis["started_at"] is not None
    assert analysis["completed_at"] is not None
    assert analysis["duration_ms"] >= 0
    assert analysis["files_analyzed"] == 2
    assert analysis["analyzer_source"] == "static"

    analysis_id = analysis["id"]
    fetched = client.get(f"/api/v1/analyses/{analysis_id}")
    assert fetched.status_code == 200
    assert len(fetched.json()["findings"]) == 2

    filtered = client.get(
        f"/api/v1/analyses/{analysis_id}/findings",
        params={"severity": "high", "source": "static"},
    )
    assert filtered.status_code == 200
    assert [item["rule"] for item in filtered.json()] == ["python.eval"]

    by_file = client.get(
        f"/api/v1/analyses/{analysis_id}/findings",
        params={"file": "debug.js"},
    )
    assert by_file.status_code == 200
    assert [item["file"] for item in by_file.json()] == ["debug.js"]
    assert client.delete(f"/api/v1/repositories/{repository_id}").status_code == 204


def test_analysis_not_found() -> None:
    missing_id = uuid4()
    assert client.get(f"/api/v1/analyses/{missing_id}").status_code == 404
    assert client.get(f"/api/v1/analyses/{missing_id}/findings").status_code == 404
