import io
import logging
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.models.repository import Repository
from app.models.user import User
from app.schemas.dashboard import GitHubImportRequest
from app.services.github import GitHubClient, GitHubImportService, HttpGitHubClient
from app.services.pull_request_review import PullRequestReviewService

METADATA = {
    "full_name": "example/sample",
    "html_url": "https://github.com/example/sample",
    "default_branch": "main",
    "description": "Sample repository",
}


def build_zip(files: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return stream.getvalue()


class FakeGitHubClient:
    def __init__(
        self,
        metadata: dict[str, object] | None = None,
        archive_content: bytes = b"",
        diff: str = "",
        pr_metadata: dict[str, object] | None = None,
        archive_error: Exception | None = None,
        diff_error: Exception | None = None,
    ) -> None:
        self._metadata: dict[str, object] = dict(metadata) if metadata else dict(METADATA)
        self._archive_content = archive_content
        self._diff = diff
        self._pr_metadata: dict[str, object] = dict(pr_metadata) if pr_metadata else {
            "number": 1,
            "title": "Test PR",
            "state": "open",
            "base": {"ref": "main"},
            "head": {"ref": "feature"},
        }
        self._archive_error = archive_error
        self._diff_error = diff_error
        self.created_files: list[Path] = []
        self.repository_calls: list[tuple[str, str]] = []
        self.fetch_archive_calls: list[tuple[str, str, str, int]] = []
        self.pull_request_calls: list[tuple[str, str, int]] = []
        self.pull_request_diff_calls: list[tuple[str, str, int]] = []

    def repository(self, owner: str, name: str) -> dict[str, object]:
        self.repository_calls.append((owner, name))
        return self._metadata

    def fetch_archive(self, owner: str, name: str, ref: str, max_size_bytes: int) -> Path:
        self.fetch_archive_calls.append((owner, name, ref, max_size_bytes))
        if self._archive_error is not None:
            raise self._archive_error
        if len(self._archive_content) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="The GitHub archive exceeds the configured size limit",
            )
        temp_file = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        temp_file.write(self._archive_content)
        temp_file.close()
        path = Path(temp_file.name)
        self.created_files.append(path)
        return path

    def pull_request(self, owner: str, name: str, number: int) -> dict[str, object]:
        self.pull_request_calls.append((owner, name, number))
        return self._pr_metadata

    def pull_request_diff(self, owner: str, name: str, number: int) -> str:
        self.pull_request_diff_calls.append((owner, name, number))
        if self._diff_error is not None:
            raise self._diff_error
        return self._diff


def _make_mock_session() -> MagicMock:
    """Create a MagicMock session that simulates SQLAlchemy flush behavior."""
    session = MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = None

    added: list[object] = []

    def _add_side_effect(obj: object) -> None:
        added.append(obj)

    def _flush_side_effect(*args: object, **kwargs: object) -> None:
        for obj in added:
            if isinstance(obj, Repository) and obj.id is None:
                obj.id = uuid4()

    session.add.side_effect = _add_side_effect
    session.flush.side_effect = _flush_side_effect
    return session


class TestPullRequestReviewService:
    def test_pull_request_review_analyzes_added_lines_only(self) -> None:
        result = PullRequestReviewService().review_diff(
            "diff --git a/app.py b/app.py\n"
            "+++ b/app.py\n"
            "@@ -1 +1 @@\n"
            "-value = eval(old_value)\n"
            "+value = eval(user_input)\n"
        )
        assert result.issues[0]["severity"] == "high"
        assert result.issues[0]["source"] == "static"
        assert result.testing_recommendations

    def test_pull_request_review_empty_diff_is_safe(self) -> None:
        result = PullRequestReviewService().review_diff("")
        assert result.issues == []

    def test_pull_request_review_detects_inner_html(self) -> None:
        result = PullRequestReviewService().review_diff(
            "diff --git a/app.jsx b/app.jsx\n"
            "+++ b/app.jsx\n"
            "@@ -1 +1 @@\n"
            "+element.innerHTML = value;\n"
        )
        assert result.issues[0]["severity"] == "high"
        assert result.issues[0]["source"] == "static"

    def test_review_diff_no_issues_found(self) -> None:
        diff = (
            "diff --git a/app.py b/app.py\n"
            "+++ b/app.py\n"
            "@@ -1 +1 @@\n"
            "+x = 1\n"
        )
        result = PullRequestReviewService().review_diff(diff)
        assert result.issues == []
        assert "Reviewed" in result.summary

    def test_review_diff_without_github_url_uses_direct_diff(self) -> None:
        service = PullRequestReviewService(client=FakeGitHubClient())

        result = service.review_diff(
            "diff --git a/app.py b/app.py\n+++ b/app.py\n+value = eval(user_input)\n"
        )

        assert result.issues[0]["severity"] == "high"
        assert result.issues[0]["source"] == "static"

    def test_review_github_pr_fetches_and_reviews(self) -> None:
        diff = (
            "diff --git a/app.py b/app.py\n"
            "+++ b/app.py\n"
            "@@ -1 +1 @@\n"
            "+value = eval(user_input)\n"
        )
        client = FakeGitHubClient(diff=diff)
        service = PullRequestReviewService(client=client)

        result = service.review_github_pr("https://github.com/owner/repo/pull/42")

        assert len(client.pull_request_calls) == 1
        assert client.pull_request_calls == [("owner", "repo", 42)]
        assert len(client.pull_request_diff_calls) == 1
        assert len(client.fetch_archive_calls) == 0
        assert result.issues[0]["file"] == "app.py"
        assert result.issues[0]["severity"] == "high"
        assert result.issues[0]["source"] == "static"

    def test_review_github_pr_invalid_url(self) -> None:
        client = FakeGitHubClient()
        service = PullRequestReviewService(client=client)

        with pytest.raises(HTTPException, match="Invalid GitHub pull request URL"):
            service.review_github_pr("https://gitlab.com/owner/repo/pull/42")

    def test_review_github_pr_without_client(self) -> None:
        service = PullRequestReviewService()

        with pytest.raises(HTTPException, match="not configured"):
            service.review_github_pr("https://github.com/owner/repo/pull/42")

    def test_review_github_pr_not_found(self) -> None:
        client = FakeGitHubClient(
            diff_error=HTTPException(
                status_code=404, detail="GitHub pull request not found"
            )
        )
        service = PullRequestReviewService(client=client)

        with pytest.raises(HTTPException, match="not found"):
            service.review_github_pr("https://github.com/owner/repo/pull/999")

    def test_review_github_pr_empty_diff(self) -> None:
        client = FakeGitHubClient(diff="")
        service = PullRequestReviewService(client=client)

        result = service.review_github_pr("https://github.com/owner/repo/pull/42")

        assert result.issues == []
        assert "No changed lines" in result.summary

    def test_review_github_pr_preserves_deterministic_findings(self) -> None:
        diff = (
            "diff --git a/app.py b/app.py\n"
            "+++ b/app.py\n"
            "@@ -1 +1 @@\n"
            "+value = eval(user_input)\n"
            "+element.innerHTML = value;\n"
        )
        client = FakeGitHubClient(diff=diff)
        service = PullRequestReviewService(client=client)

        result = service.review_github_pr("https://github.com/owner/repo/pull/1")

        static_findings = [i for i in result.issues if i.get("source") == "static"]
        assert len(static_findings) >= 1

    def test_extract_added_lines_by_file(self) -> None:
        diff = (
            "diff --git a/app.py b/app.py\n"
            "index abc..def 100644\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -1,3 +1,4 @@\n"
            " line1\n"
            "-line2\n"
            "+line2_modified\n"
            "+line3_new\n"
        )
        result = PullRequestReviewService._extract_added_lines_by_file(diff)
        assert "app.py" in result
        assert "line2_modified" in result["app.py"]
        assert "line3_new" in result["app.py"]
        assert "line1" not in result["app.py"]

    def test_extract_added_lines_handles_empty_diff(self) -> None:
        result = PullRequestReviewService._extract_added_lines_by_file("")
        assert result == {}

    def test_extract_added_lines_ignores_binary_files(self) -> None:
        diff = (
            "diff --git a/image.png b/image.png\n"
            "index abc..def 100644\n"
            "Binary files differ\n"
        )
        result = PullRequestReviewService._extract_added_lines_by_file(diff)
        assert result == {}


class TestGitHubImportServiceUrlValidation:
    def test_github_url_validation_requires_github_repository(self) -> None:
        with pytest.raises(Exception):
            GitHubImportService(MagicMock(spec=[]), FakeGitHubClient(), Settings()).import_repository(
                GitHubImportRequest(url="https://gitlab.com/example/sample")
            )

    def test_github_url_validation_accepts_github_url(self) -> None:
        service = GitHubImportService(MagicMock(), FakeGitHubClient(), Settings())
        request = GitHubImportRequest(url="https://github.com/example/sample")
        match = service.pattern.fullmatch(request.url.strip())
        assert match is not None
        assert match.groups() == ("example", "sample")

    def test_github_url_validation_rejects_non_github_url(self) -> None:
        service = GitHubImportService(MagicMock(), FakeGitHubClient(), Settings())
        request = GitHubImportRequest(url="https://gitlab.com/example/sample/repo")
        match = service.pattern.fullmatch(request.url.strip())
        assert match is None

    def test_github_url_validation_handles_git_suffix(self) -> None:
        service = GitHubImportService(MagicMock(), FakeGitHubClient(), Settings())
        request = GitHubImportRequest(url="https://github.com/example/sample.git")
        match = service.pattern.fullmatch(request.url.strip())
        assert match is not None
        assert match.groups() == ("example", "sample")


class TestGitHubImportService:
    def _make_service(
        self, client: GitHubClient, settings: Settings | None = None
    ) -> GitHubImportService:
        session = _make_mock_session()
        return GitHubImportService(session, client, settings or Settings())

    def test_github_import_persists_repository_files(self) -> None:
        archive = build_zip({
            "src/main.py": b"print('hello')",
            "README.md": b"# test",
            "node_modules/ignored.js": b"ignored",
            "image.png": b"\x89PNG\x00binary",
        })
        client = FakeGitHubClient(archive_content=archive)
        service = self._make_service(client)

        response = service.import_repository(
            GitHubImportRequest(url="https://github.com/example/sample")
        )

        assert response.status == "imported"
        assert response.name == "example/sample"
        assert response.default_branch == "main"
        assert response.file_count == 2
        assert response.id is not None
        assert response.source_url == "https://github.com/example/sample"

    def test_github_import_excludes_ignored_directories(self) -> None:
        archive = build_zip({
            "src/main.py": b"print('hello')",
            "node_modules/package/index.js": b"ignored",
            ".git/config": b"ignored",
            "__pycache__/main.cpython-314.pyc": b"ignored",
            "venv/bin/activate": b"ignored",
        })
        client = FakeGitHubClient(archive_content=archive)
        service = self._make_service(client)

        response = service.import_repository(
            GitHubImportRequest(url="https://github.com/example/sample")
        )

        assert response.file_count == 1

    def test_github_import_excludes_unsupported_extensions(self) -> None:
        archive = build_zip({
            "src/main.py": b"print('hello')",
            "notes.txt": b"plain text",
            "config.xyz": b"unknown",
            "data.json": b'{"key": "value"}',
        })
        client = FakeGitHubClient(archive_content=archive)
        service = self._make_service(client)

        response = service.import_repository(
            GitHubImportRequest(url="https://github.com/example/sample")
        )

        assert response.file_count == 2

    def test_github_import_rejects_path_traversal(self) -> None:
        archive = build_zip({"../outside.py": b"unsafe"})
        client = FakeGitHubClient(archive_content=archive)
        service = self._make_service(client)

        with pytest.raises(HTTPException, match="unsafe path"):
            service.import_repository(
                GitHubImportRequest(url="https://github.com/example/sample")
            )

    def test_github_import_rejects_oversized_archive(self) -> None:
        archive = build_zip({"file.py": b"x" * 100})
        client = FakeGitHubClient(archive_content=archive)
        settings = Settings(max_archive_size_bytes=10)
        service = self._make_service(client, settings)

        with pytest.raises(HTTPException, match="exceeds"):
            service.import_repository(
                GitHubImportRequest(url="https://github.com/example/sample")
            )

    def test_github_import_rejects_oversized_repository(self) -> None:
        archive = build_zip({
            "a.py": b"x" * 10,
            "b.py": b"y" * 10,
        })
        client = FakeGitHubClient(archive_content=archive)
        settings = Settings(max_repository_size_bytes=15)
        service = self._make_service(client, settings)

        with pytest.raises(HTTPException, match="size limit"):
            service.import_repository(
                GitHubImportRequest(url="https://github.com/example/sample")
            )

    def test_github_import_rejects_excessive_file_count(self) -> None:
        files = {f"file{i}.py": b"x" for i in range(15)}
        archive = build_zip(files)
        client = FakeGitHubClient(archive_content=archive)
        settings = Settings(max_file_count=10)
        service = self._make_service(client, settings)

        with pytest.raises(HTTPException, match="too many files"):
            service.import_repository(
                GitHubImportRequest(url="https://github.com/example/sample")
            )

    def test_github_import_cleans_up_temporary_files(self) -> None:
        archive = build_zip({"src/main.py": b"print('hello')"})
        client = FakeGitHubClient(archive_content=archive)
        service = self._make_service(client)

        service.import_repository(
            GitHubImportRequest(url="https://github.com/example/sample")
        )

        assert all(not f.exists() for f in client.created_files)

    def test_github_import_does_not_execute_repository_code(self, monkeypatch) -> None:
        mock_run = MagicMock()
        monkeypatch.setattr("subprocess.run", mock_run)
        monkeypatch.setattr("os.system", MagicMock())

        archive = build_zip({"evil.py": b"import os; os.system('echo hacked')"})
        client = FakeGitHubClient(archive_content=archive)
        service = self._make_service(client)

        service.import_repository(
            GitHubImportRequest(url="https://github.com/example/sample")
        )

        mock_run.assert_not_called()

    def test_github_import_duplicate_returns_existing(self) -> None:
        archive = build_zip({"src/main.py": b"print('hello')"})
        client = FakeGitHubClient(archive_content=archive)
        session = _make_mock_session()
        existing_repo = MagicMock()
        existing_repo.id = uuid4()
        existing_repo.name = "example/sample"
        existing_repo.source_url = "https://github.com/example/sample"
        existing_repo.default_branch = "main"
        session.query.return_value.filter_by.return_value.first.return_value = existing_repo
        session.query.return_value.filter_by.return_value.count.return_value = 5

        service = GitHubImportService(session, client, Settings())
        response = service.import_repository(
            GitHubImportRequest(url="https://github.com/example/sample")
        )

        assert response.file_count == 5
        assert response.name == "example/sample"
        assert client.fetch_archive_calls == []

    def test_github_import_uses_default_branch_when_none_supplied(self) -> None:
        archive = build_zip({"src/main.py": b"print('hello')"})
        client = FakeGitHubClient(archive_content=archive)
        service = self._make_service(client)

        service.import_repository(
            GitHubImportRequest(url="https://github.com/example/sample")
        )

        assert len(client.fetch_archive_calls) == 1
        _, _, ref, _ = client.fetch_archive_calls[0]
        assert ref == "main"

    def test_github_import_uses_explicit_branch(self) -> None:
        archive = build_zip({"src/main.py": b"print('hello')"})
        client = FakeGitHubClient(archive_content=archive)
        service = self._make_service(client)

        service.import_repository(
            GitHubImportRequest(url="https://github.com/example/sample", branch="develop")
        )

        _, _, ref, _ = client.fetch_archive_calls[0]
        assert ref == "develop"

    def test_github_import_token_never_in_response(self) -> None:
        token = "super-secret-token-12345"
        archive = build_zip({"src/main.py": b"print('hello')"})

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["authorization"] == f"Bearer {token}"
            if "/zipball/" in request.url.path:
                return httpx.Response(200, content=archive)
            return httpx.Response(200, json=METADATA)

        client = HttpGitHubClient(
            token=token, transport=httpx.MockTransport(handler)
        )
        service = self._make_service(client)

        response = service.import_repository(
            GitHubImportRequest(url="https://github.com/example/sample")
        )

        assert token not in response.model_dump_json()


class TestHttpGitHubClientRepository:
    def _make_client(self, handler, token: str | None = None) -> HttpGitHubClient:
        return HttpGitHubClient(token=token, transport=httpx.MockTransport(handler))

    def test_repository_metadata_public(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert "authorization" not in request.headers
            return httpx.Response(200, json=METADATA)

        client = self._make_client(handler)
        result = client.repository("example", "sample")
        assert result["full_name"] == "example/sample"

    def test_repository_metadata_authenticated(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["authorization"] == "Bearer test-token"
            return httpx.Response(200, json=METADATA)

        client = self._make_client(handler, token="test-token")
        result = client.repository("example", "sample")
        assert result["full_name"] == "example/sample"

    def test_repository_not_found(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"message": "Not Found"})

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException, match="not found"):
            client.repository("nonexistent", "repo")

    def test_repository_access_denied(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"message": "Forbidden"})

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException, match="access denied"):
            client.repository("private", "repo")

    def test_repository_rate_limited(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                403,
                headers={"x-ratelimit-remaining": "0"},
                json={"message": "rate limited"},
            )

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException, match="rate limit"):
            client.repository("owner", "repo")

    def test_repository_api_failure(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"message": "Server Error"})

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException, match="communicate"):
            client.repository("owner", "repo")

    def test_token_not_logged(self, caplog) -> None:
        token = "super-secret-token-12345"

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["authorization"] == f"Bearer {token}"
            return httpx.Response(200, json=METADATA)

        client = self._make_client(handler, token=token)
        with caplog.at_level(logging.DEBUG):
            client.repository("example", "sample")

        assert token not in caplog.text


class TestHttpGitHubClientFetchArchive:
    def _make_client(self, handler, token: str | None = None) -> HttpGitHubClient:
        return HttpGitHubClient(token=token, transport=httpx.MockTransport(handler))

    def test_archive_successfully_retrieved(self) -> None:
        archive_content = build_zip({"src/main.py": b"print('hello')"})

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["accept"] == "application/zip"
            assert request.headers["authorization"] == "Bearer test-token"
            return httpx.Response(
                200,
                content=archive_content,
                headers={"content-type": "application/zip"},
            )

        client = self._make_client(handler, token="test-token")
        result_path = client.fetch_archive("owner", "repo", "main", max_size_bytes=50_000_000)
        try:
            assert result_path.exists()
            with zipfile.ZipFile(result_path) as archive:
                assert "src/main.py" in archive.namelist()
        finally:
            result_path.unlink(missing_ok=True)

    def test_archive_branch_not_found(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"message": "Not Found"})

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException, match="not found"):
            client.fetch_archive("owner", "repo", "nonexistent", max_size_bytes=50_000_000)

    def test_archive_access_denied(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"message": "Forbidden"})

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException, match="access denied"):
            client.fetch_archive("owner", "repo", "main", max_size_bytes=50_000_000)

    def test_archive_oversized_rejected(self) -> None:
        large_content = b"x" * (1024 * 1024 * 5)

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=large_content)

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException, match="exceeds the configured size limit"):
            client.fetch_archive("owner", "repo", "main", max_size_bytes=1024)

    def test_archive_cleans_up_on_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"message": "Not Found"})

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException):
            client.fetch_archive("owner", "repo", "main", max_size_bytes=50_000_000)

    def test_archive_network_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException, match="Failed to retrieve"):
            client.fetch_archive("owner", "repo", "main", max_size_bytes=50_000_000)


class TestHttpGitHubClientPullRequest:
    def _make_client(self, handler, token: str | None = None) -> HttpGitHubClient:
        return HttpGitHubClient(token=token, transport=httpx.MockTransport(handler))

    def test_pull_request_metadata(self) -> None:
        pr_metadata = {
            "number": 42,
            "title": "Add new feature",
            "state": "open",
            "base": {"ref": "main"},
            "head": {"ref": "feature-branch"},
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["authorization"] == "Bearer test-token"
            return httpx.Response(200, json=pr_metadata)

        client = self._make_client(handler, token="test-token")
        result = client.pull_request("owner", "repo", 42)
        assert result["number"] == 42
        assert result["title"] == "Add new feature"

    def test_pull_request_diff(self) -> None:
        diff = (
            "diff --git a/app.py b/app.py\n"
            "+++ b/app.py\n"
            "@@ -1 +1 @@\n"
            "+value = eval(user_input)\n"
        )

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["accept"] == "application/vnd.github.v3.diff"
            return httpx.Response(200, text=diff, headers={"content-type": "text/plain"})

        client = self._make_client(handler, token="test-token")
        result = client.pull_request_diff("owner", "repo", 42)
        assert "+++ b/app.py" in result
        assert "+value = eval(user_input)" in result

    def test_pull_request_not_found(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"message": "Not Found"})

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException, match="not found"):
            client.pull_request("owner", "repo", 999)

    def test_pull_request_diff_not_found(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"message": "Not Found"})

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException, match="not found"):
            client.pull_request_diff("owner", "repo", 999)

    def test_pull_request_unauthorized(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"message": "Forbidden"})

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException, match="access denied"):
            client.pull_request("owner", "repo", 42)

    def test_pull_request_rate_limited(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                403,
                headers={"x-ratelimit-remaining": "0"},
                json={"message": "rate limited"},
            )

        client = self._make_client(handler, token="test-token")
        with pytest.raises(HTTPException, match="rate limit"):
            client.pull_request("owner", "repo", 42)


class TestPullRequestReviewEndpoint:
    def _override_auth(self) -> MagicMock:
        return MagicMock(spec=User)

    def _clear_overrides(self) -> None:
        app.dependency_overrides.clear()

    def test_endpoint_accepts_diff_only(self) -> None:
        from app.core.dependencies import get_current_user

        app.dependency_overrides[get_current_user] = self._override_auth
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/pull-requests/review",
                json={"diff": "diff --git a/app.py b/app.py\n+++ b/app.py\n+value = eval(user_input)\n"},
            )
            assert response.status_code == 200
            body = response.json()
            assert len(body["issues"]) == 1
            assert body["issues"][0]["severity"] == "high"
            assert body["issues"][0]["source"] == "static"
        finally:
            self._clear_overrides()

    def test_endpoint_requires_diff_or_github_url(self) -> None:
        from app.core.dependencies import get_current_user

        app.dependency_overrides[get_current_user] = self._override_auth
        try:
            client = TestClient(app)
            response = client.post("/api/v1/pull-requests/review", json={})
            assert response.status_code == 422
        finally:
            self._clear_overrides()

    def test_endpoint_github_url_uses_client(self) -> None:
        from app.api.v1.pull_requests import get_pull_request_review_service
        from app.core.dependencies import get_current_user

        diff = (
            "diff --git a/app.py b/app.py\n"
            "+++ b/app.py\n"
            "@@ -1 +1 @@\n"
            "+value = eval(user_input)\n"
        )

        def override_service():
            yield PullRequestReviewService(FakeGitHubClient(diff=diff), Settings())

        app.dependency_overrides[get_current_user] = self._override_auth
        app.dependency_overrides[get_pull_request_review_service] = override_service
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/pull-requests/review",
                json={"github_url": "https://github.com/owner/repo/pull/42"},
            )
            assert response.status_code == 200
            body = response.json()
            assert len(body["issues"]) == 1
            assert body["issues"][0]["source"] == "static"
        finally:
            self._clear_overrides()

    def test_endpoint_rejects_non_github_url(self) -> None:
        from app.api.v1.pull_requests import get_pull_request_review_service
        from app.core.dependencies import get_current_user

        def override_service():
            yield PullRequestReviewService(FakeGitHubClient(), Settings())

        app.dependency_overrides[get_current_user] = self._override_auth
        app.dependency_overrides[get_pull_request_review_service] = override_service
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/pull-requests/review",
                json={"github_url": "https://gitlab.com/owner/repo/pull/42"},
            )
            assert response.status_code == 422
        finally:
            self._clear_overrides()

    def test_endpoint_github_url_takes_precedence_over_diff(self) -> None:
        from app.api.v1.pull_requests import get_pull_request_review_service
        from app.core.dependencies import get_current_user

        diff = (
            "diff --git a/app.py b/app.py\n"
            "+++ b/app.py\n"
            "@@ -1 +1 @@\n"
            "+value = eval(user_input)\n"
        )

        def override_service():
            yield PullRequestReviewService(FakeGitHubClient(diff=diff), Settings())

        app.dependency_overrides[get_current_user] = self._override_auth
        app.dependency_overrides[get_pull_request_review_service] = override_service
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/pull-requests/review",
                json={"diff": "different diff", "github_url": "https://github.com/owner/repo/pull/42"},
            )
            assert response.status_code == 200
            body = response.json()
            assert len(body["issues"]) == 1
            assert body["issues"][0]["source"] == "static"
        finally:
            self._clear_overrides()
