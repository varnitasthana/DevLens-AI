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
    assert body["status"] == "completed"
    assert {finding["source"] for finding in body["findings"]} == {"static"}
    assert {finding["rule"] for finding in body["findings"]} == {
        "python.eval",
        "javascript.inner-html",
    }
    assert client.delete(f"/api/v1/repositories/{repository_id}").status_code == 204
