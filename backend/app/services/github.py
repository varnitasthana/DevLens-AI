import re
import tempfile
from pathlib import Path
from typing import Protocol

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.schemas.dashboard import GitHubImportRequest, GitHubImportResponse
from app.services.ingestion import IngestionService


class GitHubClient(Protocol):
    def repository(self, owner: str, name: str) -> dict[str, object]:
        ...

    def fetch_archive(self, owner: str, name: str, ref: str, max_size_bytes: int) -> Path:
        ...

    def pull_request(self, owner: str, name: str, number: int) -> dict[str, object]:
        ...

    def pull_request_diff(self, owner: str, name: str, number: int) -> str:
        ...


class HttpGitHubClient:
    def __init__(self, token: str | None = None, transport: httpx.BaseTransport | None = None) -> None:
        self.token = token
        self.transport = transport

    def _headers(self, accept: str) -> dict[str, str]:
        headers = {"Accept": accept}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @staticmethod
    def _is_rate_limited(response: httpx.Response) -> bool:
        return response.headers.get("x-ratelimit-remaining") == "0"

    def repository(self, owner: str, name: str) -> dict[str, object]:
        with httpx.Client(
            transport=self.transport, timeout=15, headers=self._headers("application/vnd.github+json")
        ) as client:
            try:
                response = client.get(f"https://api.github.com/repos/{owner}/{name}")
                if response.status_code == 404:
                    raise HTTPException(status_code=404, detail="GitHub repository not found")
                if response.status_code in (401, 403):
                    if self._is_rate_limited(response):
                        raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
                    raise HTTPException(status_code=403, detail="GitHub repository access denied")
                response.raise_for_status()
            except HTTPException:
                raise
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to communicate with GitHub",
                ) from exc
            return response.json()

    def fetch_archive(self, owner: str, name: str, ref: str, max_size_bytes: int) -> Path:
        temp_file = tempfile.NamedTemporaryFile(
            prefix="devlens-github-archive-", suffix=".zip", delete=False
        )
        temp_path = Path(temp_file.name)
        try:
            with httpx.Client(
                transport=self.transport, timeout=60, headers=self._headers("application/zip")
            ) as client:
                with client.stream(
                    "GET", f"https://api.github.com/repos/{owner}/{name}/zipball/{ref}"
                ) as response:
                    if response.status_code == 404:
                        raise HTTPException(
                            status_code=404, detail="GitHub repository or branch not found"
                        )
                    if response.status_code in (401, 403):
                        if self._is_rate_limited(response):
                            raise HTTPException(
                                status_code=403, detail="GitHub API rate limit exceeded"
                            )
                        raise HTTPException(
                            status_code=403, detail="GitHub repository access denied"
                        )
                    response.raise_for_status()
                    total = 0
                    for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                        total += len(chunk)
                        if total > max_size_bytes:
                            raise HTTPException(
                                status_code=413,
                                detail="The GitHub archive exceeds the configured size limit",
                            )
                        temp_file.write(chunk)
            temp_file.close()
            return temp_path
        except HTTPException:
            temp_file.close()
            temp_path.unlink(missing_ok=True)
            raise
        except httpx.HTTPError as exc:
            temp_file.close()
            temp_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve GitHub repository archive",
            ) from exc

    def pull_request(self, owner: str, name: str, number: int) -> dict[str, object]:
        with httpx.Client(
            transport=self.transport,
            timeout=15,
            headers=self._headers("application/vnd.github+json"),
        ) as client:
            try:
                response = client.get(
                    f"https://api.github.com/repos/{owner}/{name}/pulls/{number}"
                )
                if response.status_code == 404:
                    raise HTTPException(
                        status_code=404, detail="GitHub pull request not found"
                    )
                if response.status_code in (401, 403):
                    if self._is_rate_limited(response):
                        raise HTTPException(
                            status_code=403, detail="GitHub API rate limit exceeded"
                        )
                    raise HTTPException(
                        status_code=403, detail="GitHub pull request access denied"
                    )
                response.raise_for_status()
            except HTTPException:
                raise
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to communicate with GitHub",
                ) from exc
            return response.json()

    def pull_request_diff(self, owner: str, name: str, number: int) -> str:
        with httpx.Client(
            transport=self.transport,
            timeout=30,
            headers=self._headers("application/vnd.github.v3.diff"),
        ) as client:
            try:
                response = client.get(
                    f"https://api.github.com/repos/{owner}/{name}/pulls/{number}"
                )
                if response.status_code == 404:
                    raise HTTPException(
                        status_code=404, detail="GitHub pull request not found"
                    )
                if response.status_code in (401, 403):
                    if self._is_rate_limited(response):
                        raise HTTPException(
                            status_code=403, detail="GitHub API rate limit exceeded"
                        )
                    raise HTTPException(
                        status_code=403, detail="GitHub pull request access denied"
                    )
                response.raise_for_status()
            except HTTPException:
                raise
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to communicate with GitHub",
                ) from exc
            return response.text


class GitHubImportService:
    pattern = re.compile(r"^https?://github\.com/([^/]+)/([^/#]+?)(?:\.git)?/?$")

    def __init__(self, session: Session, client: GitHubClient, settings: Settings) -> None:
        self.session = session
        self.client = client
        self.settings = settings

    def import_repository(self, request: GitHubImportRequest, owner_id=None) -> GitHubImportResponse:
        match = self.pattern.fullmatch(request.url.strip())
        if not match:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid GitHub repository URL",
            )
        owner, name = match.groups()
        metadata = self.client.repository(owner, name)
        source_url = str(metadata["html_url"])
        existing = self.session.query(Repository).filter_by(source_url=source_url, owner_id=owner_id).first()
        if existing:
            file_count = self.session.query(RepositoryFile).filter_by(
                repository_id=existing.id
            ).count()
            return GitHubImportResponse(
                id=existing.id,
                name=existing.name,
                source_url=existing.source_url,
                default_branch=existing.default_branch,
                file_count=file_count,
                status="imported",
            )

        branch = request.branch or str(metadata.get("default_branch") or "main")
        repository = Repository(
            name=str(metadata["full_name"]),
            source_url=source_url,
            default_branch=branch,
            description=str(metadata["description"]) if metadata.get("description") else None,
            owner_id=owner_id,
        )
        self.session.add(repository)
        self.session.flush()

        archive_path = self.client.fetch_archive(
            owner, name, branch, self.settings.max_archive_size_bytes
        )
        try:
            files = IngestionService(self.session, self.settings).ingest_zip(repository, archive_path)
        finally:
            archive_path.unlink(missing_ok=True)

        self.session.refresh(repository)
        return GitHubImportResponse(
            id=repository.id,
            name=repository.name,
            source_url=repository.source_url,
            default_branch=repository.default_branch,
            file_count=len(files),
            status="imported",
        )
